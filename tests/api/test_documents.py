import pytest

@pytest.mark.asyncio
async def test_document_create_and_get(client):
    # Create via API
    payload = {"name": "Test Document", "url": "https://example.com"}
    resp = await client.post("/documents/", json=payload)
    assert resp.status_code == 202, resp.text
    created = resp.json()
    doc_id = created["document_uuid"]

    # Fetch via API
    get_resp = await client.get(f"/documents/{doc_id}/")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["name"] == "Test Document"
    assert data["url"] == "https://example.com"
    assert data["summary"] is None
    assert data["status"] in {"PENDING", "PROCESSING", "SUCCESS", "FAILED"}

@pytest.mark.asyncio
async def test_list_documents(client):
    # seed two docs
    await client.post("/documents/", json={"name": "A", "url": "https://a.test"})
    await client.post("/documents/", json={"name": "B", "url": "https://b.test"})

    resp = await client.get("/documents?limit=10&offset=0")
    assert resp.status_code == 200
    items = resp.json()
    assert isinstance(items, list)
    # newest first per our Fake repo
    assert {items[0]["name"], items[1]["name"]} == {"A", "B"}
