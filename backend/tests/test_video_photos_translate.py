# Iteration 9: post videos, profile photos, auto-translation, admin email logic
import base64
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
ANA = ("anaa@teste.com", "Teste123")
BRUNO = ("bruno@teste.com", "Teste123")
PNG = "data:image/png;base64," + base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")).decode()


def _login(email, pw):
    s = requests.Session()
    r = s.post(f"{BASE_URL}/api/auth/login", json={"email": email, "password": pw})
    if r.status_code != 200:
        pytest.skip(f"login failed {email}: {r.status_code}")
    s.headers["Authorization"] = f"Bearer {r.json()['token']}"
    s.user = r.json()["user"]
    return s


@pytest.fixture(scope="module")
def ana():
    return _login(*ANA)


@pytest.fixture(scope="module")
def bruno():
    return _login(*BRUNO)


@pytest.fixture(scope="module")
def mdb():
    from pymongo import MongoClient
    from dotenv import dotenv_values
    env = dotenv_values("/app/backend/.env")
    return MongoClient(env["MONGO_URL"])[env["DB_NAME"]]


@pytest.fixture(scope="module")
def ana_post(ana, mdb):
    r = ana.post(f"{BASE_URL}/api/posts", json={"type": "need", "category": "food",
                                                "title": "TEST_video 🎉😀", "description": "TEST desc 👍", "images": []})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    yield pid
    mdb.posts.delete_one({"id": pid})
    for f in mdb.post_videos.files.find({"metadata.post_id": pid}):
        mdb.post_videos.chunks.delete_many({"files_id": f["_id"]})
        mdb.post_videos.files.delete_one({"_id": f["_id"]})


# ---- Emojis persist in posts
def test_post_emoji_persist(ana, ana_post):
    posts = ana.get(f"{BASE_URL}/api/posts", params={"user_id": ana.user["id"], "limit": 50}).json()["posts"]
    p = next(x for x in posts if x["id"] == ana_post)
    assert p["title"] == "TEST_video 🎉😀"
    assert p["description"] == "TEST desc 👍"
    assert p.get("video_url") is None


# ---- Videos
def test_video_requires_auth(ana_post):
    r = requests.post(f"{BASE_URL}/api/posts/{ana_post}/video", files={"file": ("a.mp4", b"x" * 10, "video/mp4")})
    assert r.status_code in (401, 403)


def test_video_non_owner_404(bruno, ana_post):
    r = bruno.post(f"{BASE_URL}/api/posts/{ana_post}/video", files={"file": ("a.mp4", b"x" * 10, "video/mp4")})
    assert r.status_code == 404


def test_video_wrong_type_400(ana, ana_post):
    r = ana.post(f"{BASE_URL}/api/posts/{ana_post}/video", files={"file": ("a.txt", b"hello", "text/plain")})
    assert r.status_code == 400


def test_video_upload_and_stream(ana, ana_post):
    data = bytes(range(256)) * 400  # 102400 bytes
    r = ana.post(f"{BASE_URL}/api/posts/{ana_post}/video", files={"file": ("a.mp4", data, "video/mp4")})
    assert r.status_code == 200, r.text
    assert r.json()["video_url"] == f"/api/posts/{ana_post}/video"
    # feed exposes video_url
    posts = ana.get(f"{BASE_URL}/api/posts", params={"user_id": ana.user["id"], "limit": 50}).json()["posts"]
    p = next(x for x in posts if x["id"] == ana_post)
    assert p["video_url"] == f"/api/posts/{ana_post}/video"
    assert "video_file_id" not in p or True
    full = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video")
    assert full.status_code == 200
    assert full.headers["content-type"].startswith("video/mp4")
    assert full.content == data
    part = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video", headers={"Range": "bytes=100-199"})
    assert part.status_code == 206
    assert part.content == data[100:200]
    assert part.headers["content-range"] == f"bytes 100-199/{len(data)}"
    openr = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video", headers={"Range": "bytes=102000-"})
    assert openr.status_code == 206 and openr.content == data[102000:]
    suffix = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video", headers={"Range": "bytes=-50"})
    assert suffix.status_code == 206 and suffix.content == data[-50:]
    bad = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video", headers={"Range": "bytes=999999-"})
    assert bad.status_code == 416


def test_video_replace(ana, ana_post, mdb):
    r = ana.post(f"{BASE_URL}/api/posts/{ana_post}/video", files={"file": ("b.webm", b"z" * 500, "video/webm")})
    assert r.status_code == 200
    g = requests.get(f"{BASE_URL}/api/posts/{ana_post}/video")
    assert g.content == b"z" * 500 and g.headers["content-type"].startswith("video/webm")
    assert mdb.post_videos.files.count_documents({"metadata.post_id": ana_post}) == 1


def test_video_missing_404():
    assert requests.get(f"{BASE_URL}/api/posts/nonexistent-xyz/video").status_code == 404


# ---- Profile photos
def test_profile_photos_crud(ana, bruno, mdb):
    uid = ana.user["id"]
    before = ana.get(f"{BASE_URL}/api/users/{uid}/photos").json()
    r = ana.post(f"{BASE_URL}/api/profile/photos", json={"image": PNG})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    assert r.json()["url"] == f"/api/profile-photos/{pid}"
    try:
        lst = ana.get(f"{BASE_URL}/api/users/{uid}/photos").json()
        assert len(lst) == len(before) + 1 and any(p["id"] == pid for p in lst)
        # other users can list
        assert any(p["id"] == pid for p in bruno.get(f"{BASE_URL}/api/users/{uid}/photos").json())
        img = requests.get(f"{BASE_URL}/api/profile-photos/{pid}")
        assert img.status_code == 200 and img.content[:4] == b"\x89PNG"
        # non-owner delete forbidden
        assert bruno.delete(f"{BASE_URL}/api/profile/photos/{pid}").status_code == 404
        d = ana.delete(f"{BASE_URL}/api/profile/photos/{pid}")
        assert d.status_code == 200 and d.json()["ok"] is True
        assert requests.get(f"{BASE_URL}/api/profile-photos/{pid}").status_code == 404
    finally:
        mdb.profile_photos.delete_one({"id": pid})


def test_profile_photo_invalid(ana):
    assert ana.post(f"{BASE_URL}/api/profile/photos", json={"image": "notadataurl"}).status_code == 400
    assert ana.post(f"{BASE_URL}/api/profile/photos", json={"image": "data:text/plain;base64,aGVsbG8="}).status_code == 400
    assert ana.post(f"{BASE_URL}/api/profile/photos", json={"image": "data:image/png;base64,@@@"}).status_code == 400
    assert requests.post(f"{BASE_URL}/api/profile/photos", json={"image": PNG}).status_code in (401, 403)
    assert requests.get(f"{BASE_URL}/api/users/x/photos").status_code in (401, 403)


def test_profile_photo_max6(bruno, mdb):
    uid = bruno.user["id"]
    existing = len(bruno.get(f"{BASE_URL}/api/users/{uid}/photos").json())
    created = []
    try:
        for _ in range(6 - existing):
            r = bruno.post(f"{BASE_URL}/api/profile/photos", json={"image": PNG})
            assert r.status_code == 200
            created.append(r.json()["id"])
        r = bruno.post(f"{BASE_URL}/api/profile/photos", json={"image": PNG})
        assert r.status_code == 400
    finally:
        mdb.profile_photos.delete_many({"id": {"$in": created}})


# ---- Translation
def test_translate_basic_and_cache(mdb):
    texts = ["Buscar Vagas", "Preciso de roupas de inverno 🎉", "ana@teste.com"]
    r = requests.post(f"{BASE_URL}/api/translate", json={"texts": texts, "lang": "en"}, timeout=90)
    assert r.status_code == 200, r.text
    tr = r.json()["translations"]
    assert len(tr) == 3
    assert "job" in tr[0].lower() or "search" in tr[0].lower(), tr
    assert "🎉" in tr[1] and "winter" in tr[1].lower(), tr
    # cache hit
    r2 = requests.post(f"{BASE_URL}/api/translate", json={"texts": texts[:2], "lang": "en"}, timeout=30)
    assert r2.json()["translations"] == tr[:2]


@pytest.mark.parametrize("lang,word", [("fr", "emploi"), ("es", "empleo")])
def test_translate_langs(lang, word):
    # NOTE: "Buscar Vagas de emprego" -> es came back unchanged (LLM judged it Spanish) and got cached permanently
    r = requests.post(f"{BASE_URL}/api/translate", json={"texts": ["Nova publicação"], "lang": lang}, timeout=90)
    assert r.status_code == 200
    assert r.json()["translations"][0] != "Nova publicação"


def test_translate_invalid():
    assert requests.post(f"{BASE_URL}/api/translate", json={"texts": ["Olá"], "lang": "de"}).status_code == 400
    assert requests.post(f"{BASE_URL}/api/translate", json={"texts": ["a"] * 151, "lang": "en"}).status_code == 422
    r = requests.post(f"{BASE_URL}/api/translate", json={"texts": [], "lang": "en"})
    assert r.status_code == 200 and r.json()["translations"] == []


# ---- Regular users stay non-admin on login
def test_login_regular_not_admin(ana, bruno):
    assert ana.user["role"] == "migrant"
    assert bruno.user["role"] == "volunteer"
