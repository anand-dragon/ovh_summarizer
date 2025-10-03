import pytest
from fastapi import status
from app.api.main import app
from app.api import depends

# We'll use your actual URL here
URL = "https://www.google.com"
NAME = "Article Summaries"

class _SpyRedis:
    def __init__(self):
        self.jobs = []

    async def ping(self) -> bool:
        return True

    async def enqueue_job(self, fn, arg):
        self.jobs.append((fn, arg))

@pytest.mark.asyncio
async def test_smart_submission_create_conflict_resummarize(client):
    """
    1) First POST -> creates new doc (202), queues job, progress = 0.0
    2) Second POST with different name but same URL -> 409
    3) Third POST with same name+URL -> resummarize original (202), same UUID, queues job again
    """

    # swap in a spy redis just for this test (keeps router clean)
    spy = _SpyRedis()
    app.dependency_overrides[depends.get_redis] = lambda: spy

    # 1) create
    resp1 = await client.post("/documents/", json={"name": NAME, "url": URL})
    assert resp1.status_code == status.HTTP_202_ACCEPTED, resp1.text
    created = resp1.json()
    doc_id = created["document_uuid"]
    assert created["name"] == NAME
    assert created["url"] == URL
    assert created["status"] == "PENDING"
    assert created["data_progress"] == 0.0  # computed field

    # Enqueue should have happened once
    assert len(spy.jobs) == 1
    assert spy.jobs[0][0] == "process_document"
    assert spy.jobs[0][1] == doc_id

    # 2) conflict (same URL, different name) → 409
    resp_conflict = await client.post("/documents/", json={"name": "Different Name", "url": URL})
    assert resp_conflict.status_code == status.HTTP_409_CONFLICT
    detail = resp_conflict.json().get("detail", "")
    assert "exists" in detail.lower()

    # 3) resummarize (same name + same URL) → 202, same UUID, queues again
    resp3 = await client.post("/documents/", json={"name": NAME, "url": URL})
    assert resp3.status_code == status.HTTP_202_ACCEPTED, resp3.text
    again = resp3.json()
    assert again["document_uuid"] == doc_id  # same document, not a new row

    # Enqueue should be called again (total 2)
    assert len(spy.jobs) == 2
    assert spy.jobs[1][0] == "process_document"
    assert spy.jobs[1][1] == doc_id

    # clean override
    app.dependency_overrides.pop(depends.get_redis, None)
