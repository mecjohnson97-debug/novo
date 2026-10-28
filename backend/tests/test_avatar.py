# Profile avatar upload/delete/get + feed avatar_version fields
import base64
import io
import os
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')

# 1x1 PNG
PNG = base64.b64encode(base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=='
)).decode()


def _login(email, pw):
    r = requests.post(f"{BASE_URL}/api/auth/login", json={'email': email, 'password': pw})
    if r.status_code != 200:
        pytest.skip(f"login failed {email}")
    return r.json()


@pytest.fixture(scope='module')
def maria():
    return _login('maria@teste.com', 'Teste123!')


@pytest.fixture(scope='module')
def h(maria):
    return {'Authorization': f"Bearer {maria['token']}"}


class TestAvatar:
    def test_no_token(self):
        r = requests.put(f"{BASE_URL}/api/profile/avatar", json={'image': f'data:image/png;base64,{PNG}'})
        assert r.status_code in (401, 403)
        r = requests.delete(f"{BASE_URL}/api/profile/avatar")
        assert r.status_code in (401, 403)

    def test_bad_mime(self, h):
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={'image': 'data:text/plain;base64,aGVsbG8='})
        assert r.status_code == 400

    def test_bad_base64(self, h):
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={'image': 'data:image/png;base64,@@@notb64'})
        assert r.status_code == 400

    def test_missing_field(self, h):
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={})
        assert r.status_code == 422

    def test_too_large(self, h):
        big = base64.b64encode(b'\x00' * 700_000).decode()
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={'image': f'data:image/jpeg;base64,{big}'})
        assert r.status_code == 413

    def test_upload_get_delete_flow(self, h, maria):
        uid = maria['user']['id']
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={'image': f'data:image/png;base64,{PNG}'})
        assert r.status_code == 200
        v = r.json()['avatar_version']
        assert isinstance(v, int)
        g = requests.get(f"{BASE_URL}/api/users/{uid}/avatar?v={v}")
        assert g.status_code == 200
        assert g.headers['content-type'].startswith('image/png')
        assert g.content == base64.b64decode(PNG)
        prof = requests.get(f"{BASE_URL}/api/profile", headers=h).json()
        assert prof.get('avatar_version') == v
        # delete
        d = requests.delete(f"{BASE_URL}/api/profile/avatar", headers=h)
        assert d.status_code == 200 and d.json()['avatar_version'] is None
        g = requests.get(f"{BASE_URL}/api/users/{uid}/avatar?v=x{v}")
        assert g.status_code == 404
        prof = requests.get(f"{BASE_URL}/api/profile", headers=h).json()
        assert not prof.get('avatar_version')
        # login also returns no avatar_version
        assert not _login('maria@teste.com', 'Teste123!')['user'].get('avatar_version')

    def test_unknown_user_404(self):
        assert requests.get(f"{BASE_URL}/api/users/does-not-exist/avatar").status_code == 404

    def test_posts_include_avatar_version(self, h, maria):
        uid = maria['user']['id']
        r = requests.put(f"{BASE_URL}/api/profile/avatar", headers=h, json={'image': f'data:image/png;base64,{PNG}'})
        v = r.json()['avatar_version']
        try:
            posts = requests.get(f"{BASE_URL}/api/posts", headers=h).json()
            items = posts if isinstance(posts, list) else posts.get('posts') or posts.get('items') or []
            assert items, 'no posts'
            for p in items:
                if p.get('user') and p['user'].get('role') != 'assistant':
                    assert 'id' in p['user'] and 'avatar_version' in p['user']
            mine = requests.get(f"{BASE_URL}/api/posts?user_id={uid}", headers=h).json()['posts']
            if mine:
                assert mine[0]['user']['avatar_version'] == v
            withc = [p for p in items if p.get('comment_count')]
            if withc:
                cs = requests.get(f"{BASE_URL}/api/posts/{withc[0]['id']}/comments").json()
                for c in cs:
                    if c.get('user'):
                        assert 'avatar_version' in c['user']
        finally:
            pass  # leave avatar uploaded for UI testing
