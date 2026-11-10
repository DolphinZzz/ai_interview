import json
import unittest
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.backoffice.deps import get_current_admin
from app.core.config import settings
from app.db.session import get_db


class FakeResult:
    def __init__(self, rows):
        self.rows = rows

    def all(self):
        return self.rows


class FakeDB:
    def __init__(self, resume, user):
        self.resume = resume
        self.user = user

    async def scalar(self, query):
        return 1

    async def execute(self, query):
        return FakeResult([(self.resume, self.user)])

    async def get(self, model, identifier):
        return self.resume if identifier == self.resume.id else None


class BackofficeResumeRouteTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = TemporaryDirectory()
        self.original_upload_root = settings.UPLOAD_ROOT
        settings.UPLOAD_ROOT = self.temp_dir.name
        resume_dir = Path(self.temp_dir.name) / "resumes"
        resume_dir.mkdir()
        self.pdf_path = resume_dir / "candidate.pdf"
        self.pdf_path.write_bytes(b"%PDF-1.4 test")
        self.resume = SimpleNamespace(
            id=12,
            user_id=4,
            file_url=str(self.pdf_path),
            file_name="candidate.pdf",
            target_position="后端工程师",
            status="completed",
            extracted_text="PDF 直接抽取内容",
            parsed_content=json.dumps({"name": "张三"}),
            analysis=json.dumps({"score": 90}),
            created_at=datetime(2026, 8, 20, 10, 0, 0),
        )
        self.user = SimpleNamespace(
            id=4,
            email="candidate@example.com",
            first_name="张",
            last_name="三",
        )

    def tearDown(self):
        settings.UPLOAD_ROOT = self.original_upload_root
        self.temp_dir.cleanup()

    def _client(self):
        from app.api.backoffice.v1.resumes import router

        app = FastAPI()
        app.include_router(router, prefix="/api/v1/backoffice/resumes")

        async def override_db():
            yield FakeDB(self.resume, self.user)

        async def override_admin():
            return SimpleNamespace(id=1)

        app.dependency_overrides[get_db] = override_db
        app.dependency_overrides[get_current_admin] = override_admin
        return TestClient(app)

    def test_admin_can_list_resumes_and_filter_by_status(self):
        response = self._client().get("/api/v1/backoffice/resumes?status=completed")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["total"], 1)
        self.assertEqual(data["items"][0]["user_email"], "candidate@example.com")
        self.assertEqual(data["items"][0]["file_name"], "candidate.pdf")

    def test_admin_detail_returns_pdf_text_and_ai_results(self):
        response = self._client().get("/api/v1/backoffice/resumes/12")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["extracted_text"], "PDF 直接抽取内容")
        self.assertEqual(data["parsed_content"], {"name": "张三"})
        self.assertEqual(data["analysis"], {"score": 90})

    def test_admin_can_download_resume_pdf(self):
        response = self._client().get("/api/v1/backoffice/resumes/12/download")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers["content-type"], "application/pdf")
        self.assertEqual(response.content, b"%PDF-1.4 test")

    def test_download_rejects_file_paths_outside_resume_storage(self):
        self.resume.file_url = str(Path(self.temp_dir.name) / "outside.pdf")
        Path(self.resume.file_url).write_bytes(b"not a resume")

        response = self._client().get("/api/v1/backoffice/resumes/12/download")

        self.assertEqual(response.status_code, 404)

    def test_list_rejects_invalid_pagination(self):
        client = self._client()

        self.assertEqual(client.get("/api/v1/backoffice/resumes?page=0").status_code, 422)
        self.assertEqual(client.get("/api/v1/backoffice/resumes?per_page=101").status_code, 422)
