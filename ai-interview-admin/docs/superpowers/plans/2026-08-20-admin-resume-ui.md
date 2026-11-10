# 管理员简历展示 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 Vue 管理端展示并下载管理员有权限访问的用户简历。

**Architecture:** 在既有 axios 实例上新增 `resumeApi`，列表和详情各使用一个 Vue 页面并由 Vue Router 懒加载；下载响应以 Blob 处理，避免将认证信息放在链接中。

**Tech Stack:** Vue 3, Vue Router, Axios, Vite, Node test runner.

---

### Task 1: 简历 API 封装

**Files:**
- Modify: `src/api/index.js`
- Test: `tests/resume-api.test.mjs`

- [ ] 写失败测试，断言 `list`、`detail` 和 `download` 使用 `/resumes` 后台路径，且下载请求使用 `responseType: 'blob'`。
- [ ] 运行 `node --test tests/resume-api.test.mjs`，确认因 API 不存在失败。
- [ ] 增加 `resumeApi` 三个方法。
- [ ] 重新运行测试确认通过。

### Task 2: 简历列表和导航

**Files:**
- Create: `src/views/Resumes.vue`
- Modify: `src/router/index.js`
- Modify: `src/App.vue`

- [ ] 写失败构建检查，确认新页面可被路由懒加载。
- [ ] 实现筛选、分页、加载、空状态和详情入口。
- [ ] 增加侧栏入口和 `/resumes` 路由。
- [ ] 运行 `npm run build`。

### Task 3: 简历详情及下载

**Files:**
- Create: `src/views/ResumeDetail.vue`
- Modify: `src/router/index.js`

- [ ] 写失败构建检查，确认详情路由引用的组件存在。
- [ ] 实现顶部摘要、三个标签页、JSON 格式化、空状态和 Blob 下载。
- [ ] 增加 `/resumes/:id` 路由。
- [ ] 运行 `npm run build`，并检查生成产物包含简历页面 chunk。
