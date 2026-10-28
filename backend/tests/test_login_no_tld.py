# Login: non-TLD emails must not trigger 422 (EmailStr removed from UserLogin)
import os
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')


def test_login_no_tld_returns_401_not_422():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "nouser@notld", "password": "123456"})
    assert r.status_code == 401, r.text
    assert r.json().get("detail") == "Invalid credentials"


def test_login_admin_at_admin_not_422():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@admin", "password": "wrong"})
    assert r.status_code == 401, r.text


def test_login_missing_email_422():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"password": "x"})
    assert r.status_code == 422


def test_admin_login_ok():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "admin@fieledeus.com", "password": "FielAdmin2026!"})
    assert r.status_code == 200
    d = r.json()
    assert d["user"]["role"] == "admin" and d["token"]
    s = requests.get(f"{BASE_URL}/api/admin/stats", headers={"Authorization": f"Bearer {d['token']}"})
    assert s.status_code == 200


def test_maria_login_ok():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": "maria@teste.com", "password": "Teste123!"})
    assert r.status_code == 200
    assert r.json()["user"]["role"] != "admin"
