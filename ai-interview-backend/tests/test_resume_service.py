import unittest
from pathlib import Path

from app.services.client import resume_service as resume_module


class FakeDB:
    def __init__(self):
        self.added = []

    def add(self, value):
        self.added.append(value)

    async def commit(self):
        return None

    async def refresh(self, value):
        if value.id is None:
            value.id = 1


class ResumeServiceTests(unittest.IsolatedAsyncioTestCase):
    async def test_upload_and_parse_persists_pdf_extracted_text(self):
        original_upload_dir = resume_module.UPLOAD_DIR
        original_extract = resume_module.ResumeService._extract_pdf_text
        original_parse = resume_module.AIService.parse_resume
        original_analyze = resume_module.AIService.analyze_resume
        temp_dir = self.enterContext(_TemporaryDirectory())

        resume_module.UPLOAD_DIR = temp_dir
        resume_module.ResumeService._extract_pdf_text = staticmethod(
            lambda path: "PDF 原始文本\n第二行"
        )
        resume_module.AIService.parse_resume = staticmethod(
            lambda text: _resolved({"name": "张三"})
        )
        resume_module.AIService.analyze_resume = staticmethod(
            lambda parsed, position: _resolved({"score": 90})
        )
        self.addCleanup(setattr, resume_module, "UPLOAD_DIR", original_upload_dir)
        self.addCleanup(
            setattr, resume_module.ResumeService, "_extract_pdf_text", original_extract
        )
        self.addCleanup(setattr, resume_module.AIService, "parse_resume", original_parse)
        self.addCleanup(setattr, resume_module.AIService, "analyze_resume", original_analyze)

        db = FakeDB()
        await resume_module.ResumeService.upload_and_parse(
            db=db,
            user_id=7,
            file_content=b"%PDF-fake",
            file_name="../../resume.pdf",
            target_position="后端工程师",
        )

        self.assertEqual(db.added[0].extracted_text, "PDF 原始文本\n第二行")
        self.assertEqual(db.added[0].file_name, "resume.pdf")
        self.assertEqual(Path(db.added[0].file_url).parent, Path(temp_dir))


async def _resolved(value):
    return value


class _TemporaryDirectory:
    def __enter__(self):
        import tempfile
        self.directory = tempfile.TemporaryDirectory()
        return self.directory.name

    def __exit__(self, exc_type, exc_value, traceback):
        self.directory.cleanup()
