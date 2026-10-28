# Tests: password reset (forgot/reset) + chat appointments (create/respond/visibility)
import os
import uuid
from datetime import datetime, timedelta, timezone

import bcrypt
import pytest
import requests
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv('/app/frontend/.env')
load_dotenv('/app/backend/.env')
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
mdb = MongoClient(os.environ['MONGO_URL'])[os.environ['DB_NAME']]

ANA = ('anaa@teste.com', 'Teste123')
BRUNO = ('bruno@teste.com', 'Teste123')


def login(email, pw):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={'email': email, 'password': pw})
    assert r.status_code == 200, r.text
    d = r.json()
    return d.get('token') or d.get('access_token'), d['user']


@pytest.fixture(scope='module')
def ana():
    t, u = login(*ANA)
    return {'h': {'Authorization': f'Bearer {t}'}, 'u': u}


@pytest.fixture(scope='module')
def bruno():
    t, u = login(*BRUNO)
    return {'h': {'Authorization': f'Bearer {t}'}, 'u': u}


def tomorrow():
    return (datetime.now(timezone.utc) + timedelta(days=1)).strftime('%Y-%m-%d')


# ---------- Password reset ----------
class TestPasswordReset:
    def test_forgot_unknown_email_generic(self):
        r = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={'email': f'nobody_{uuid.uuid4().hex[:6]}@x.com'})
        assert r.status_code == 200
        assert 'código' in r.json()['message']

    def test_forgot_rate_limit_and_wrong_code(self):
        SINK = 'delivered@resend.dev'
        u = mdb.users.find_one({'email': SINK})
        if not u:
            pytest.skip('sink user missing')
        mdb.password_resets.delete_many({'user_id': u['id']})
        r1 = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={'email': SINK.upper()})
        assert r1.status_code == 200, r1.text
        assert mdb.password_resets.find_one({'user_id': u['id']}) is not None
        r2 = requests.post(f"{BASE_URL}/api/auth/forgot-password", json={'email': SINK})
        assert r2.status_code == 429
        r3 = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': SINK, 'code': '000000', 'new_password': 'NovaSenha1'})
        # ~1e-6 chance of collision
        assert r3.status_code == 400

    def test_lockout_after_5_attempts(self, ana):
        uid = ana['u']['id']
        now = datetime.now(timezone.utc)
        mdb.password_resets.update_one({'user_id': uid}, {'$set': {
            'user_id': uid, 'code_hash': bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode(), 'attempts': 0,
            'created_at': now.isoformat(), 'expires_at': (now + timedelta(minutes=15)).isoformat()}}, upsert=True)
        for _ in range(5):
            r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '654321', 'new_password': 'NovaSenha1'})
            assert r.status_code == 400
        # correct code now locked
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '123456', 'new_password': 'NovaSenha1'})
        assert r.status_code == 400
        mdb.password_resets.delete_many({'user_id': uid})

    def test_expired_code(self, ana):
        uid = ana['u']['id']
        now = datetime.now(timezone.utc)
        mdb.password_resets.update_one({'user_id': uid}, {'$set': {
            'user_id': uid, 'code_hash': bcrypt.hashpw(b'123456', bcrypt.gensalt()).decode(), 'attempts': 0,
            'created_at': (now - timedelta(minutes=20)).isoformat(), 'expires_at': (now - timedelta(minutes=5)).isoformat()}}, upsert=True)
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '123456', 'new_password': 'NovaSenha1'})
        assert r.status_code == 400
        mdb.password_resets.delete_many({'user_id': uid})

    def test_successful_reset_then_restore(self, ana):
        uid = ana['u']['id']
        now = datetime.now(timezone.utc)
        mdb.password_resets.update_one({'user_id': uid}, {'$set': {
            'user_id': uid, 'code_hash': bcrypt.hashpw(b'112233', bcrypt.gensalt()).decode(), 'attempts': 0,
            'created_at': now.isoformat(), 'expires_at': (now + timedelta(minutes=15)).isoformat()}}, upsert=True)
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '112233', 'new_password': 'NovaSenha1'})
        assert r.status_code == 200, r.text
        assert mdb.password_resets.find_one({'user_id': uid}) is None
        # old pw fails, new works
        assert requests.post(f"{BASE_URL}/api/auth/login", json={'email': ANA[0], 'password': 'Teste123'}).status_code == 401
        login(ANA[0], 'NovaSenha1')
        # reused code fails
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '112233', 'new_password': 'Teste123'})
        assert r.status_code == 400
        # restore
        mdb.users.update_one({'id': uid}, {'$set': {'password': bcrypt.hashpw(b'Teste123', bcrypt.gensalt()).decode()}})
        login(*ANA)

    def test_reset_validation(self):
        r = requests.post(f"{BASE_URL}/api/auth/reset-password", json={'email': ANA[0], 'code': '12', 'new_password': 'x'})
        assert r.status_code == 422


# ---------- Appointments ----------
@pytest.fixture(scope='module')
def created_ids():
    ids = []
    yield ids
    mdb.messages.delete_many({'$or': [{'id': {'$in': ids}}, {'appointment_update.ref_id': {'$in': ids}}]})


def create(ana, bruno, **kw):
    body = {'to_user_id': bruno['u']['id'], 'date': tomorrow(), 'time': '14:30', 'mode': 'in_person',
            'info': 'TEST_ Rua X, 12', 'acknowledged': True}
    body.update(kw)
    return requests.post(f"{BASE_URL}/api/appointments", json=body, headers=ana['h'])


class TestAppointments:
    def test_validation(self, ana, bruno):
        assert create(ana, bruno, mode='teleport').status_code == 400
        assert create(ana, bruno, acknowledged=False).status_code == 400
        assert create(ana, bruno, date='2020-01-01').status_code == 400
        assert create(ana, bruno, to_user_id='nonexistent-id').status_code == 404
        assert create(ana, bruno, to_user_id=ana['u']['id']).status_code == 404
        assert create(ana, bruno, info='x' * 501).status_code == 422
        assert create(ana, bruno, time='2pm').status_code == 422
        assert create(ana, bruno, date='2026-13-40').status_code == 400

    def test_unauth(self, bruno):
        r = requests.post(f"{BASE_URL}/api/appointments", json={'to_user_id': bruno['u']['id'], 'date': tomorrow(), 'time': '10:00', 'mode': 'video', 'acknowledged': True})
        assert r.status_code in (401, 403)

    def test_create_and_visibility_accept(self, ana, bruno, created_ids):
        r = create(ana, bruno)
        assert r.status_code == 200, r.text
        m = r.json()
        created_ids.append(m['id'])
        assert m['appointment']['status'] == 'pending'
        assert m['appointment']['info'] == 'TEST_ Rua X, 12'
        # recipient doesn't see info
        msgs = requests.get(f"{BASE_URL}/api/messages/{ana['u']['id']}", headers=bruno['h']).json()
        mine = next(x for x in msgs if x['id'] == m['id'])
        assert mine['appointment']['info'] is None and mine['appointment']['has_info'] is True
        # sender sees info
        msgs = requests.get(f"{BASE_URL}/api/messages/{bruno['u']['id']}", headers=ana['h']).json()
        assert next(x for x in msgs if x['id'] == m['id'])['appointment']['info'] == 'TEST_ Rua X, 12'
        # sender cannot accept
        r = requests.put(f"{BASE_URL}/api/appointments/{m['id']}/respond", json={'action': 'accept'}, headers=ana['h'])
        assert r.status_code == 403
        # recipient can't cancel
        r = requests.put(f"{BASE_URL}/api/appointments/{m['id']}/respond", json={'action': 'cancel'}, headers=bruno['h'])
        assert r.status_code == 403
        # accept
        r = requests.put(f"{BASE_URL}/api/appointments/{m['id']}/respond", json={'action': 'accept'}, headers=bruno['h'])
        assert r.status_code == 200 and r.json()['status'] == 'accepted'
        msgs = requests.get(f"{BASE_URL}/api/messages/{ana['u']['id']}", headers=bruno['h']).json()
        assert next(x for x in msgs if x['id'] == m['id'])['appointment']['info'] == 'TEST_ Rua X, 12'
        upd = [x for x in msgs if x.get('appointment_update', {}).get('ref_id') == m['id']]
        assert len(upd) == 1 and 'aceitou' in upd[0]['message']
        # already responded
        r = requests.put(f"{BASE_URL}/api/appointments/{m['id']}/respond", json={'action': 'decline'}, headers=bruno['h'])
        assert r.status_code == 400

    def test_decline_and_cancel(self, ana, bruno, created_ids):
        m1 = create(ana, bruno, mode='video', info='').json(); created_ids.append(m1['id'])
        msgs = requests.get(f"{BASE_URL}/api/messages/{ana['u']['id']}", headers=bruno['h']).json()
        assert next(x for x in msgs if x['id'] == m1['id'])['appointment']['has_info'] is False
        r = requests.put(f"{BASE_URL}/api/appointments/{m1['id']}/respond", json={'action': 'decline'}, headers=bruno['h'])
        assert r.status_code == 200 and r.json()['status'] == 'declined'
        # declined: info still hidden for recipient
        m2 = create(ana, bruno, mode='phone').json(); created_ids.append(m2['id'])
        r = requests.put(f"{BASE_URL}/api/appointments/{m2['id']}/respond", json={'action': 'cancel'}, headers=ana['h'])
        assert r.status_code == 200 and r.json()['status'] == 'cancelled'
        msgs = requests.get(f"{BASE_URL}/api/messages/{ana['u']['id']}", headers=bruno['h']).json()
        assert next(x for x in msgs if x['id'] == m2['id'])['appointment']['info'] is None

    def test_recipient_can_propose_too(self, ana, bruno, created_ids):
        r = create(bruno, ana, to_user_id=ana['u']['id'], mode='other')
        assert r.status_code == 200
        created_ids.append(r.json()['id'])

    def test_outsider_and_unknown(self, ana, bruno, created_ids):
        m = create(ana, bruno).json(); created_ids.append(m['id'])
        # register outsider
        em = f"test_out_{uuid.uuid4().hex[:6]}@teste.com"
        rr = requests.post(f"{BASE_URL}/api/auth/register", json={'email': em, 'password': 'Teste123', 'name': 'TEST Out', 'role': 'migrant'})
        if rr.status_code != 200:
            pytest.skip(f"register failed {rr.status_code} {rr.text[:200]}")
        t = rr.json().get('token') or rr.json().get('access_token')
        r = requests.put(f"{BASE_URL}/api/appointments/{m['id']}/respond", json={'action': 'accept'}, headers={'Authorization': f'Bearer {t}'})
        assert r.status_code == 404
        mdb.users.delete_one({'email': em})
        r = requests.put(f"{BASE_URL}/api/appointments/nonexistent/respond", json={'action': 'accept'}, headers=bruno['h'])
        assert r.status_code == 404
