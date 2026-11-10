<template>
  <div>
    <div class="page-header">
      <h1>简历管理</h1>
      <div class="filters">
        <input v-model="keyword" placeholder="搜索姓名/邮箱..." @input="debouncedSearch" />
        <select v-model="statusFilter" @change="handleStatusChange">
          <option value="">全部状态</option>
          <option value="parsing">解析中</option>
          <option value="completed">已完成</option>
          <option value="failed">失败</option>
        </select>
      </div>
    </div>

    <div class="card">
      <div v-if="loading" class="state-message">正在加载简历...</div>
      <div v-else-if="error" class="state-message error-message">{{ error }}</div>
      <template v-else>
        <table v-if="resumes.length">
          <thead>
            <tr>
              <th>用户</th>
              <th>文件名</th>
              <th>目标岗位</th>
              <th>状态</th>
              <th>上传时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="resume in resumes" :key="resume.id">
              <td>
                <div>{{ resume.user_name || '未填写姓名' }}</div>
                <div class="email">{{ resume.user_email }}</div>
              </td>
              <td>{{ resume.file_name || '-' }}</td>
              <td>{{ resume.target_position || '-' }}</td>
              <td><span :class="['badge', statusClass(resume.status)]">{{ statusText(resume.status) }}</span></td>
              <td>{{ formatDate(resume.created_at) }}</td>
              <td><router-link :to="`/resumes/${resume.id}`" class="btn-primary btn-sm detail-link">详情</router-link></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="state-message">暂无符合条件的简历</div>

        <div v-if="total > perPage" class="pagination">
          <button class="btn-sm" :disabled="page <= 1" @click="changePage(page - 1)">上一页</button>
          <span>{{ page }} / {{ totalPages }}</span>
          <button class="btn-sm" :disabled="page >= totalPages" @click="changePage(page + 1)">下一页</button>
        </div>
      </template>
    </div>
  </div>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { resumeApi } from '../api'

const resumes = ref([])
const total = ref(0)
const page = ref(1)
const perPage = 20
const keyword = ref('')
const statusFilter = ref('')
const loading = ref(false)
const error = ref('')
let searchTimer = null
let latestRequest = 0

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / perPage)))

function formatDate(value) {
  return value ? new Date(value).toLocaleString('zh-CN') : '-'
}

function statusText(status) {
  return { pending: '待解析', parsing: '解析中', completed: '已完成', failed: '失败' }[status] || status || '-'
}

function statusClass(status) {
  return { pending: 'badge-yellow', parsing: 'badge-yellow', completed: 'badge-green', failed: 'badge-red' }[status] || 'badge-yellow'
}

async function loadResumes() {
  const requestId = ++latestRequest
  loading.value = true
  error.value = ''
  try {
    const data = await resumeApi.list({
      page: page.value,
      per_page: perPage,
      keyword: keyword.value.trim() || undefined,
      status: statusFilter.value || undefined
    })
    if (requestId !== latestRequest) return
    resumes.value = data.items || []
    total.value = data.total || 0
  } catch (e) {
    if (requestId !== latestRequest) return
    resumes.value = []
    total.value = 0
    error.value = e?.message || '简历列表加载失败，请稍后重试'
  } finally {
    if (requestId === latestRequest) loading.value = false
  }
}

function debouncedSearch() {
  clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    page.value = 1
    loadResumes()
  }, 300)
}

function handleStatusChange() {
  page.value = 1
  loadResumes()
}

function changePage(nextPage) {
  page.value = nextPage
  loadResumes()
}

onMounted(loadResumes)
onBeforeUnmount(() => clearTimeout(searchTimer))
</script>

<style scoped>
.page-header { display: flex; justify-content: space-between; align-items: center; gap: 16px; margin-bottom: 20px; }
.page-header h1 { font-size: 20px; }
.filters { display: flex; gap: 10px; }
.filters input { width: 240px; }
.filters select { width: 140px; }
.email { margin-top: 3px; color: #6b7280; font-size: 12px; }
.detail-link { color: white; display: inline-block; }
.state-message { padding: 36px 16px; color: #6b7280; text-align: center; }
.error-message { color: #dc2626; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 16px; padding: 16px 0 0; color: #6b7280; font-size: 13px; }

@media (max-width: 760px) {
  .page-header { align-items: flex-start; flex-direction: column; }
  .filters { width: 100%; }
  .filters input { flex: 1; width: auto; min-width: 0; }
}
</style>
