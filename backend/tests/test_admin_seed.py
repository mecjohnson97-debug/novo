# Admin seed + admin endpoints access control tests
import os
import subprocess
import time
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
ADMIN = {"email": "admin@fieledeus.com", "password": "FielAdmin2026!"}
MARIA = {"email": "maria@teste.com", "password": "Teste123!"}


def _env(key):
    with open('/app/backend/.env') as f:
        for line in f:
            if line.startswith(key + '='):
                return line.split('=', 1)[1].strip().strip('"')


@pytest.fixture(scope="module")
def mdb():
    c = MongoClient(_env('MONGO_URL'))
    yield c[_env('DB_NAME')]
    c.close()


def login(creds):
    return requests.post(f"{BASE_URL}/api/auth/login", json=creds, timeout=20)


def wait_backend():
    for _ in range(40):
        try:
            if login(ADMIN).status_code in (200, 401):
                return
        except Exception:
            pass
        time.sleep(1)


# Admin login
class TestAdminLogin:
    def test_admin_login(self):
        r = login(ADMIN)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["user"]["role"] == "admin"
        assert d["user"]["email"] == ADMIN["email"]
        assert "password" not in d["user"]
        assert isinstance(d["token"], str) and d["token"]

    def test_admin_wrong_password(self):
        r = login({"email": ADMIN["email"], "password": "wrong"})
        assert r.status_code == 401

    def test_admin_bcrypt_hash(self, mdb):
        u = mdb.users.find_one({"email": ADMIN["email"]})
        assert u["password"].startswith("$2b$")

    @pytest.mark.parametrize("path", ["/api/admin/stats", "/api/admin/users", "/api/admin/posts"])
    def test_admin_endpoints(self, path):
        tok = login(ADMIN).json()["token"]
        r = requests.get(f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
        assert r.status_code == 200, r.text
        d = r.json()
        if path.endswith("stats"):
            assert isinstance(d["total_users"], int) and d["total_users"] >= 2
        else:
            assert isinstance(d, list)
        if path.endswith("users"):
            assert all("password" not in u for u in d)
            assert any(u["email"] == ADMIN["email"] for u in d)


# Non-admin access control
class TestNonAdmin:
    @pytest.mark.parametrize("path", ["/api/admin/stats", "/api/admin/users", "/api/admin/posts"])
    def test_maria_forbidden(self, path):
        r = login(MARIA)
        assert r.status_code == 200
        assert r.json()["user"]["role"] != "admin"
        tok = r.json()["token"]
        r = requests.get(f"{BASE_URL}{path}", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
        assert r.status_code == 403

    def test_no_token(self):
        r = requests.get(f"{BASE_URL}/api/admin/stats", timeout=20)
        assert r.status_code in (401, 403)

    def test_maria_feed(self):
        tok = login(MARIA).json()["token"]
        r = requests.get(f"{BASE_URL}/api/posts", headers={"Authorization": f"Bearer {tok}"}, timeout=20)
        assert r.status_code == 200
        d = r.json()
        posts = d if isinstance(d, list) else d.get("posts", [])
        assert len(posts) > 0


# Seed idempotency across restarts + password/role reset
class TestSeedIdempotent:
    def test_restart_no_duplicate(self, mdb):
        subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True)
        time.sleep(3)
        wait_backend()
        assert mdb.users.count_documents({"email": ADMIN["email"]}) == 1
        assert login(ADMIN).status_code == 200

    def test_seed_resets_changed_password_and_role(self, mdb):
        import bcrypt
        orig = mdb.users.find_one({"email": ADMIN["email"]})
        mdb.users.update_one({"email": ADMIN["email"]}, {"$set": {
            "password": bcrypt.hashpw(b"other", bcrypt.gensalt()).decode(), "role": "migrant"}})
        assert login(ADMIN).status_code == 401
        subprocess.run(["sudo", "supervisorctl", "restart", "backend"], check=True)
        time.sleep(3)
        wait_backend()
        r = login(ADMIN)
        assert r.status_code == 200
        assert r.json()["user"]["role"] == "admin"
        u = mdb.users.find_one({"email": ADMIN["email"]})
        assert u["id"] == orig["id"]
        assert mdb.users.count_documents({"email": ADMIN["email"]}) == 1
