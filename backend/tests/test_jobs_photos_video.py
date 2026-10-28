# Regression: job search (free sources, regions), profile photos, post video upload, lazy emergentintegrations import
import os, io, base64, subprocess, sys, uuid
import pytest
import requests

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL').rstrip('/')
EMAIL = "teste.fotos@example.com"
PASSWORD = "Teste123!"
REGIONS = ['br', 'pt', 'fr', 'be', 'ch', 'es', 'it', 'de', 'gb', 'us', 'ca', 'latam', 'remote']
PNG_1PX = base64.b64encode(base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==")).decode()


@pytest.fixture(scope="module")
def token():
    r = requests.post(f"{BASE_URL}/api/auth/login", json={"email": EMAIL, "password": PASSWORD}, timeout=20)
    if r.status_code != 200:
        email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        r = requests.post(f"{BASE_URL}/api/auth/register", json={"email": email, "password": PASSWORD, "name": "TEST User", "role": "migrant"}, timeout=20)
    assert r.status_code == 200, r.text
    pytest.USER_ID = r.json()["user"]["id"]
    return r.json().get("token") or r.json().get("access_token")


@pytest.fixture(scope="module")
def h(token):
    return {"Authorization": f"Bearer {token}"}


def _cleanup_post(pid):
    from pymongo import MongoClient
    from dotenv import dotenv_values
    from gridfs import GridFSBucket
    env = dotenv_values('/app/backend/.env')
    db = MongoClient(env['MONGO_URL'])[env['DB_NAME']]
    b = GridFSBucket(db, bucket_name='post_videos')
    for f in db['post_videos.files'].find({'metadata.post_id': pid}):
        b.delete(f['_id'])
    db.posts.delete_one({'id': pid})


# Jobs
class TestJobs:
    def test_regions(self):
        r = requests.get(f"{BASE_URL}/api/jobs/regions", timeout=20)
        assert r.status_code == 200
        vals = [x['value'] for x in r.json()]
        assert vals == REGIONS

    def test_search_br_default(self):
        r = requests.get(f"{BASE_URL}/api/jobs/search", params={"query": "emprego", "region": "br"}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d['total'] > 0 and len(d['jobs']) > 0
        assert d['region'] == 'br'
        j = d['jobs'][0]
        for k in ('id', 'title', 'company', 'url', 'source'):
            assert k in j and j[k]

    @pytest.mark.parametrize("region", REGIONS)
    def test_search_all_regions(self, region):
        r = requests.get(f"{BASE_URL}/api/jobs/search", params={"query": "emprego", "region": region}, timeout=90)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d['region'] == region
        print(region, d['total'], d.get('sources'))
        assert d['total'] > 0, f"no jobs for {region}"

    def test_search_specific_term(self):
        r = requests.get(f"{BASE_URL}/api/jobs/search", params={"query": "desenvolvedor", "region": "remote"}, timeout=90)
        assert r.status_code == 200
        print("dev remote", r.json()['total'])

    def test_invalid_region_fallback(self):
        r = requests.get(f"{BASE_URL}/api/jobs/search", params={"query": "emprego", "region": "zz"}, timeout=90)
        assert r.status_code == 200


# Profile photos
class TestPhotos:
    def test_add_list_get_delete(self, h, token):
        uid = pytest.USER_ID
        existing = requests.get(f"{BASE_URL}/api/users/{uid}/photos", headers=h, timeout=20).json()
        for p in existing:
            requests.delete(f"{BASE_URL}/api/profile/photos/{p['id']}", headers=h, timeout=20)
        r = requests.post(f"{BASE_URL}/api/profile/photos", headers=h, json={"image": f"data:image/png;base64,{PNG_1PX}"}, timeout=20)
        assert r.status_code == 200, r.text
        pid = r.json()['id']
        lst = requests.get(f"{BASE_URL}/api/users/{uid}/photos", headers=h, timeout=20).json()
        assert any(p['id'] == pid for p in lst)
        img = requests.get(f"{BASE_URL}/api/profile-photos/{pid}", timeout=20)
        assert img.status_code == 200 and img.headers['content-type'].startswith('image/png')
        d = requests.delete(f"{BASE_URL}/api/profile/photos/{pid}", headers=h, timeout=20)
        assert d.status_code == 200
        assert requests.get(f"{BASE_URL}/api/profile-photos/{pid}", timeout=20).status_code == 404

    def test_invalid_image(self, h):
        r = requests.post(f"{BASE_URL}/api/profile/photos", headers=h, json={"image": "notadataurl"}, timeout=20)
        assert r.status_code == 400


# Post video
class TestVideo:
    @pytest.fixture(scope="class")
    def post_id(self, h):
        r = requests.post(f"{BASE_URL}/api/posts", headers=h, json={"type": "need", "category": "food", "title": "TEST_video post", "description": "TEST video", "images": []}, timeout=20)
        assert r.status_code == 200, r.text
        pid = r.json()['id']
        yield pid
        _cleanup_post(pid)  # no DELETE /api/posts endpoint exists -> clean via DB

    def test_upload_octet_stream_mp4(self, h, post_id):
        data = b"\x00\x00\x00\x18ftypmp42" + os.urandom(2048)
        r = requests.post(f"{BASE_URL}/api/posts/{post_id}/video", headers=h,
                          files={"file": ("clip.mp4", io.BytesIO(data), "application/octet-stream")}, timeout=60)
        assert r.status_code == 200, r.text
        assert r.json()['video_url'] == f"/api/posts/{post_id}/video"
        g = requests.get(f"{BASE_URL}/api/posts/{post_id}/video", timeout=30)
        assert g.status_code == 200 and g.headers['content-type'].startswith('video/mp4')
        assert len(g.content) == len(data)
        rg = requests.get(f"{BASE_URL}/api/posts/{post_id}/video", headers={"Range": "bytes=0-99"}, timeout=30)
        assert rg.status_code == 206 and len(rg.content) == 100

    def test_upload_octet_stream_mov(self, h, post_id):
        r = requests.post(f"{BASE_URL}/api/posts/{post_id}/video", headers=h,
                          files={"file": ("clip.MOV", io.BytesIO(os.urandom(1024)), "application/octet-stream")}, timeout=60)
        assert r.status_code == 200, r.text
        g = requests.get(f"{BASE_URL}/api/posts/{post_id}/video", timeout=30)
        assert g.headers['content-type'].startswith('video/quicktime')

    def test_reject_non_video(self, h, post_id):
        r = requests.post(f"{BASE_URL}/api/posts/{post_id}/video", headers=h,
                          files={"file": ("doc.txt", io.BytesIO(b"hello"), "application/octet-stream")}, timeout=30)
        assert r.status_code == 400

    def test_post_has_video_in_feed(self, h, post_id):
        r = requests.get(f"{BASE_URL}/api/posts", headers=h, params={"limit": 50}, timeout=20)
        posts = r.json().get('posts', r.json()) if isinstance(r.json(), dict) else r.json()
        p = next((x for x in posts if x['id'] == post_id), None)
        assert p is not None and p.get('has_video') is True
        assert 'video_file_id' not in p or isinstance(p['video_file_id'], str)


# Lazy import: server.py must import without emergentintegrations
def test_server_imports_without_emergentintegrations():
    code = ("import sys, builtins\n"
            "real=builtins.__import__\n"
            "def fake(n,*a,**k):\n"
            "    if n.startswith('emergentintegrations'): raise ImportError('blocked')\n"
            "    return real(n,*a,**k)\n"
            "builtins.__import__=fake\n"
            "sys.path.insert(0,'/app/backend')\n"
            "import server\nprint('OK')\n")
    p = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60, cwd="/app/backend")
    assert "OK" in p.stdout, p.stderr[-2000:]
