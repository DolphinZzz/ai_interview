# 管理员简历查看 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增加后台管理员简历列表、详情、原始 PDF 文本查看和受保护下载能力。

**Architecture:** 复用现有 FastAPI 后台鉴权和 `Resume` 模型，在数据库保存 `pdfplumber` 原始文本；新增后台简历路由与轻量服务逻辑，文件通过鉴权后的 `FileResponse` 返回，并移除简历目录的公共静态暴露。

**Tech Stack:** FastAPI, SQLAlchemy async, Alembic, pytest.

---

### Task 1: 数据模型与上传持久化

**Files:**
- Modify: `app/models/resume.py`
- Modify: `app/services/client/resume_service.py`
- Create: `migrations/versions/<new>_add_extracted_text_to_resume.py`
- Test: `tests/test_resume_service.py`

- [ ] 写测试：断言上传流程将 `_extract_pdf_text` 返回的文本写入 `Resume.extracted_text`，并断言详情返回该文本。
- [ ] 运行测试确认在字段不存在时失败。
- [ ] 增加可空 Text 字段，上传成功解析后赋值并提交。
- [ ] 添加 Alembic upgrade/downgrade 迁移。
- [ ] 运行单测和迁移静态检查。

### Task 2: 后台列表与详情接口

**Files:**
- Create: `app/api/backoffice/v1/resumes.py`
- Modify: `app/route/router_registry.py`
- Test: `tests/test_backoffice_resumes.py`

- [ ] 写失败测试：管理员列表分页、关键词/状态过滤，以及详情反序列化字段。
- [ ] 实现 `/api/v1/backoffice/resumes` 列表和 `/{resume_id}` 详情，全部依赖 `get_current_admin`。
- [ ] 使用 `select(Resume).join(User)`，返回用户 id、邮箱、姓名及简历元数据；不存在返回统一 404。
- [ ] 运行路由单测确认通过。

### Task 3: 鉴权下载与静态资源收敛

**Files:**
- Modify: `app/api/backoffice/v1/resumes.py`
- Modify: `app/api/client/v1/resume.py` only if shared helper is needed
- Modify: `app/route/route.py`
- Test: `tests/test_backoffice_resumes.py`

- [ ] 写失败测试：管理员下载存在文件返回 PDF 响应，缺失文件返回 404；无后台 token 不能访问。
- [ ] 实现下载接口，使用 `FileResponse`，路径必须来自数据库记录且文件存在。
- [ ] 将静态挂载限制为头像目录（或移除公共挂载并保留受控接口），确保简历不可匿名读取。
- [ ] 运行全部测试并检查 OpenAPI 路由注册。

### Task 4: 收尾验证

**Files:**
- No new files.

- [ ] 执行 `pytest -q`。
- [ ] 执行 `python -m compileall app`。
- [ ] 检查 git diff，确认只包含本功能文件和迁移。
