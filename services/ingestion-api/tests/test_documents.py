import io
import pytest


@pytest.mark.asyncio
async def test_upload_valid_pdf(client):
    fake_pdf = io.BytesIO(b"%PDF-1.4 fake pdf content")
    fake_pdf.name = "test.pdf"

    response = await client.post(
        "/documents/",
        files={"file": ("test.pdf", fake_pdf, "application/pdf")},
    )

    assert response.status_code == 202
    data = response.json()
    assert data["filename"] == "test.pdf"
    assert data["status"] == "pending"
    assert data["mime_type"] == "application/pdf"
    assert "id" in data


@pytest.mark.asyncio
async def test_upload_invalid_mime_type(client):
    fake_file = io.BytesIO(b"not a pdf")

    response = await client.post(
        "/documents/",
        files={"file": ("test.txt", fake_file, "text/plain")},
    )

    assert response.status_code == 415


@pytest.mark.asyncio
async def test_upload_file_too_large(client):
    large_file = io.BytesIO(b"x" * (21 * 1024 * 1024))

    response = await client.post(
        "/documents/",
        files={"file": ("large.pdf", large_file, "application/pdf")},
    )

    assert response.status_code == 413


@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["database"] == "ok"
    assert data["redis"] == "ok"