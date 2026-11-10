<template>
  <div class="resume-detail">
    <div class="page-header">
      <div>
        <router-link to="/resumes" class="back-link">返回简历列表</router-link>
        <h1>简历详情</h1>
      </div>
      <button class="btn-primary" :disabled="downloading || loading || !detail" @click="downloadResume">
        {{ downloading ? '下载中...' : '下载 PDF' }}
      </button>
    </div>

    <div v-if="loading" class="state-message">正在加载简历详情...</div>
    <div v-else-if="error" class="state-message error-message">
      <p>{{ error }}</p>
      <button class="btn-sm retry-button" @click="loadDetail">重新加载</button>
    </div>

    <template v-else-if="detail">
      <section class="card summary-card">
        <div class="summary-item">
          <span class="info-label">用户</span>
          <strong>{{ userName }}</strong>
          <span class="subtle-text">{{ detail.user?.email || '-' }}</span>
        </div>
        <div class="summary-item">
          <span class="info-label">简历文件</span>
          <span>{{ detail.file_name || '-' }}</span>
        </div>
        <div class="summary-item">
          <span class="info-label">目标岗位</span>
          <span>{{ detail.target_position || '-' }}</span>
        </div>
        <div class="summary-item">
          <span class="info-label">解析状态</span>
          <span :class="['badge', statusClass(detail.status)]">{{ statusText(detail.status) }}</span>
        </div>
        <div class="summary-item">
          <span class="info-label">上传时间</span>
          <span>{{ formatDate(detail.created_at) }}</span>
        </div>
      </section>

      <p v-if="downloadError" class="download-error">{{ downloadError }}</p>

      <section class="card content-card">
        <div class="tabs" role="tablist" aria-label="简历内容">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            type="button"
            :class="['tab-button', { active: activeTab === tab.key }]"
            :aria-selected="activeTab === tab.key"
            @click="activeTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <div v-if="activeTab === 'extracted'" class="tab-panel">
          <pre v-if="detail.extracted_text" class="text-content">{{ detail.extracted_text }}</pre>
          <div v-else class="empty-state">该简历尚无 PDF 原始解析文本。历史上传记录不会回填该字段。</div>
        </div>

        <div v-else-if="activeTab === 'parsed'" class="tab-panel">
          <pre v-if="hasValue(detail.parsed_content)" class="json-content">{{ formatJson(detail.parsed_content) }}</pre>
          <div v-else class="empty-state">该简历尚无 AI 结构化解析结果。</div>
        </div>

        <div v-else class="tab-panel">
          <pre v-if="hasValue(detail.analysis)" class="json-content">{{ formatJson(detail.analysis) }}</pre>
          <div v-else class="empty-state">该简历尚无 AI 分析结果。</div>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { resumeApi } from '../api'

const route = useRoute()
const detail = ref(null)
const loading = ref(true)
const error = ref('')
const downloading = ref(false)
const downloadError = ref('')
const activeTab = ref('extracted')

const tabs = [
  { key: 'extracted', label: 'PDF 原始文本' },
  { key: 'parsed', label: 'AI 结构化解析' },
  { key: 'analysis', label: 'AI 分析' }
]

const userName = computed(() => {
  const user = detail.value?.user
  const name = [user?.first_name, user?.last_name].filter(Boolean).join(' ')
  return name || '未填写姓名'
})

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '-'
}

function statusText(status) {
  return { pending: '待解析', parsing: '解析中', completed: '已完成', failed: '失败' }[status] || status || '-'
}

function statusClass(status) {
  return { pending: 'badge-yellow', parsing: 'badge-yellow', completed: 'badge-green', failed: 'badge-red' }[status] || 'badge-yellow'
}

function hasValue(value) {
  if (value === null || value === undefined || value === '') return false
  if (Array.isArray(value)) return value.length > 0
  return typeof value !== 'object' || Object.keys(value).length > 0
}

function formatJson(value) {
  if (typeof value === 'string') {
    try {
      return JSON.stringify(JSON.parse(value), null, 2)
    } catch {
      return value
    }
  }
  return JSON.stringify(value, null, 2)
}

function fileNameFromDisposition(disposition) {
  if (!disposition) return detail.value?.file_name || 'resume.pdf'
  const encodedMatch = disposition.match(/filename\*=UTF-8''([^;]+)/i)
  if (encodedMatch) return decodeURIComponent(encodedMatch[1])
  const plainMatch = disposition.match(/filename="?([^";]+)"?/i)
  return plainMatch?.[1] || detail.value?.file_name || 'resume.pdf'
}

async function loadDetail() {
  loading.value = true
  error.value = ''
  try {
    detail.value = await resumeApi.detail(route.params.id)
  } catch (e) {
    detail.value = null
    error.value = e?.message || '简历详情加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

async function downloadResume() {
  downloading.value = true
  downloadError.value = ''
  try {
    const response = await resumeApi.download(route.params.id)
    const blob = response?.data instanceof Blob ? response.data : response
    if (!(blob instanceof Blob)) throw new Error('下载文件格式不正确')

    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = fileNameFromDisposition(response?.headers?.['content-disposition'])
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (e) {
    downloadError.value = e?.message || 'PDF 下载失败，请稍后重试'
  } finally {
    downloading.value = false
  }
}

onMounted(loadDetail)
</script>

<style scoped>
.page-header { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; margin-bottom: 20px; }
.page-header h1 { margin-top: 8px; font-size: 20px; }
.back-link { color: #6b7280; font-size: 14px; }
.summary-card { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 20px; margin-bottom: 16px; }
.summary-item { display: flex; min-width: 0; flex-direction: column; gap: 5px; font-size: 14px; overflow-wrap: anywhere; }
.info-label { color: #6b7280; font-size: 12px; }
.subtle-text { color: #6b7280; font-size: 12px; }
.download-error { margin: 0 0 16px; color: #b91c1c; font-size: 13px; }
.content-card { padding: 0; overflow: hidden; }
.tabs { display: flex; border-bottom: 1px solid #e5e7eb; overflow-x: auto; }
.tab-button { flex: 0 0 auto; border-radius: 0; background: transparent; color: #6b7280; padding: 13px 18px 11px; border-bottom: 2px solid transparent; }
.tab-button:hover { background: #f9fafb; color: #374151; }
.tab-button.active { border-bottom-color: #4f46e5; color: #4338ca; font-weight: 600; }
.tab-panel { min-height: 300px; padding: 20px; }
.text-content, .json-content { margin: 0; color: #374151; font: 13px/1.7 ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; white-space: pre-wrap; overflow-wrap: anywhere; }
.empty-state, .state-message { padding: 48px 16px; color: #6b7280; text-align: center; }
.error-message { color: #b91c1c; }
.retry-button { margin-top: 14px; background: #e5e7eb; color: #374151; }

@media (max-width: 920px) {
  .summary-card { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (max-width: 560px) {
  .page-header { align-items: flex-start; flex-direction: column; }
  .summary-card { grid-template-columns: 1fr; }
  .page-header .btn-primary { width: 100%; }
  .tab-panel { padding: 16px; }
}
</style>
