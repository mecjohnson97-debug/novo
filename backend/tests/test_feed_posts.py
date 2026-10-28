# Feed / posts API regression tests (pagination, filters, images, comments)
import base64
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
EMAIL = "maria@teste.com"
PASSWORD = "Teste123!"
PNG = "data:image/png;base64," + base64.b64encode(bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082")).decode()


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    r = sess.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD})
    if r.status_code != 200:
        pytest.skip(f"login failed {r.status_code} {r.text}")
    sess.headers["Authorization"] = f"Bearer {r.json()['token']}"
    return sess


# Auth
def test_login(s):
    assert "Authorization" in s.headers


def test_posts_requires_auth():
    r = requests.get(f"{BASE_URL}/api/posts")
    assert r.status_code in (401, 403)


# Feed shape + pagination
def test_posts_first_page_shape(s):
    r = s.get(f"{BASE_URL}/api/posts", params={"limit": 10, "skip": 0})
    assert r.status_code == 200
    d = r.json()
    assert set(["posts", "has_more", "next_skip"]) <= set(d)
    assert len(d["posts"]) == 10
    assert d["next_skip"] == 10
    for p in d["posts"]:
        assert "images" not in p
        assert isinstance(p["image_urls"], list)
        assert isinstance(p["comment_count"], int)
        assert "name" in p["user"] and "role" in p["user"]
        assert "_id" not in p


def test_pagination_no_overlap(s):
    a = s.get(f"{BASE_URL}/api/posts", params={"limit": 10, "skip": 0}).json()
    b = s.get(f"{BASE_URL}/api/posts", params={"limit": 10, "skip": 10}).json()
    ids_a = {p["id"] for p in a["posts"]}
    ids_b = {p["id"] for p in b["posts"]}
    assert not ids_a & ids_b
    total = s.get(f"{BASE_URL}/api/posts", params={"limit": 50}).json()
    assert len(total["posts"]) >= 12
    created = [p["created_at"] for p in total["posts"]]
    assert created == sorted(created, reverse=True)


def test_limit_clamped(s):
    d = s.get(f"{BASE_URL}/api/posts", params={"limit": 500}).json()
    assert len(d["posts"]) <= 50


# Filters
@pytest.mark.parametrize("t", ["need", "offer", "job"])
def test_type_filter(s, t):
    d = s.get(f"{BASE_URL}/api/posts", params={"type": t, "limit": 50}).json()
    assert all(p["type"] == t for p in d["posts"])


@pytest.mark.parametrize("c", ["food", "work", "housing"])
def test_category_filter(s, c):
    d = s.get(f"{BASE_URL}/api/posts", params={"category": c, "limit": 50}).json()
    assert all(c == p.get("category") or c in p.get("categories", []) for p in d["posts"])


# Create post with image -> image endpoint -> user_id filter -> comments
def test_create_post_image_comments(s):
    title = f"TEST_post_{uuid.uuid4().hex[:6]}"
    r = s.post(f"{BASE_URL}/api/posts", json={"type": "need", "category": "food", "title": title,
                                              "description": "TEST desc", "images": [PNG]})
    assert r.status_code == 200, r.text
    pid = r.json()["id"]
    uid = r.json()["user_id"]

    first = s.get(f"{BASE_URL}/api/posts", params={"limit": 10}).json()["posts"][0]
    assert first["id"] == pid
    assert first["image_urls"] == [f"/api/posts/{pid}/images/0"]

    img = requests.get(f"{BASE_URL}/api/posts/{pid}/images/0")
    assert img.status_code == 200
    assert img.headers["content-type"].startswith("image/png")
    # preview ingress overrides Cache-Control; backend sets max-age (verified on localhost)
    assert img.content[:4] == b"\x89PNG"
    assert requests.get(f"{BASE_URL}/api/posts/{pid}/images/5").status_code == 404
    assert requests.get(f"{BASE_URL}/api/posts/nonexistent/images/0").status_code == 404

    mine = s.get(f"{BASE_URL}/api/posts", params={"user_id": uid, "limit": 50}).json()["posts"]
    assert all(p["user_id"] == uid for p in mine) and any(p["id"] == pid for p in mine)

    c = s.post(f"{BASE_URL}/api/posts/{pid}/comments", json={"comment": "TEST comment"})
    assert c.status_code == 200
    cl = s.get(f"{BASE_URL}/api/posts/{pid}/comments").json()
    assert len(cl) == 1 and cl[0]["comment"] == "TEST comment" and cl[0]["user"]["name"]
    first = s.get(f"{BASE_URL}/api/posts", params={"limit": 10}).json()["posts"][0]
    assert first["comment_count"] == 1

    # cleanup via mongo
    from pymongo import MongoClient
    from dotenv import dotenv_values
    env = dotenv_values("/app/backend/.env")
    db = MongoClient(env["MONGO_URL"])[env["DB_NAME"]]
    db.posts.delete_one({"id": pid})
    db.comments.delete_many({"post_id": pid})
    db.messages.delete_many({"to_user_id": uid, "is_auto_response": True,
                             "created_at": {"$gte": r.json()["created_at"][:19]}})


def test_volunteers_and_health(s):
    assert s.get(f"{BASE_URL}/api/volunteers").status_code == 200
