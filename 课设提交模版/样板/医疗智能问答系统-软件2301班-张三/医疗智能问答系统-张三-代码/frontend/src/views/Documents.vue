<template>
  <div class="documents-container">
    <div class="sidebar">
      <div class="new-chat-btn"><el-button type="primary" @click="$router.push('/chat')" :icon="ChatDotRound" round>返回问答</el-button></div>
      <el-menu :default-active="activeRoute" class="sidebar-menu" @select="handleMenuSelect">
        <el-menu-item index="/chat"><el-icon><ChatDotRound /></el-icon><span>智能问答</span></el-menu-item>
        <el-menu-item index="/documents"><el-icon><Document /></el-icon><span>知识库管理</span></el-menu-item>
      </el-menu>
    </div>
    <div class="main-area">
      <div class="docs-header"><h2>知识库管理</h2>
        <el-upload :show-file-list="false" :before-upload="beforeUpload" :http-request="handleUpload" accept=".pdf,.docx,.doc">
          <el-button type="primary" :icon="Upload">上传文档</el-button>
        </el-upload>
      </div>
      <div v-if="uploading" class="upload-progress"><el-alert title="文档上传处理中，正在向量化..." type="info" :closable="false" /></div>
      <div class="docs-list">
        <el-table :data="documents" style="width: 100%" v-loading="loading">
          <el-table-column prop="filename" label="文件名" min-width="200"><template #default="{ row }"><div class="filename-cell"><el-icon :size="20" :color="getFileIconColor(row.file_type)"><Document /></el-icon><span>{{ row.filename }}</span></div></template></el-table-column>
          <el-table-column prop="file_type" label="类型" width="100"><template #default="{ row }"><el-tag>{{ row.file_type }}</el-tag></template></el-table-column>
          <el-table-column prop="file_size" label="大小" width="120"><template #default="{ row }">{{ formatFileSize(row.file_size) }}</template></el-table-column>
          <el-table-column prop="status" label="状态" width="120"><template #default="{ row }"><el-tag :type="getStatusType(row.status)">{{ getStatusText(row.status) }}</el-tag></template></el-table-column>
          <el-table-column prop="upload_time" label="上传时间" width="180"><template #default="{ row }">{{ formatDate(row.upload_time) }}</template></el-table-column>
          <el-table-column label="操作" width="100" fixed="right"><template #default="{ row }"><el-button type="danger" :icon="Delete" size="small" @click="handleDelete(row)">删除</el-button></template></el-table-column>
        </el-table>
        <div v-if="documents.length === 0 && !loading" class="empty-docs"><el-empty description="还没有上传任何文档"><el-button type="primary" @click="triggerUpload">上传第一个文档</el-button></el-empty></div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { ChatDotRound, Document, Upload, Delete } from '@element-plus/icons-vue'
import { getDocuments, uploadDocument, deleteDocument } from '../api'

const router = useRouter()
const activeRoute = ref('/documents')
const documents = ref([])
const loading = ref(false)
const uploading = ref(false)

onMounted(() => { loadDocuments() })

const loadDocuments = async () => {
  loading.value = true
  try { const res = await getDocuments(); documents.value = res.documents || [] } catch (error) { ElMessage.error('加载文档列表失败') } finally { loading.value = false }
}

const beforeUpload = (file) => {
  const allowedTypes = ['.pdf', '.docx', '.doc']
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!allowedTypes.includes(ext)) { ElMessage.error('仅支持 PDF、Word 格式文件'); return false }
  if (file.size > 50 * 1024 * 1024) { ElMessage.error('文件大小不能超过 50MB'); return false }
  return true
}

const handleUpload = async (options) => {
  uploading.value = true
  try { await uploadDocument(options.file); ElMessage.success('文档上传成功，知识库已更新'); await loadDocuments() } catch (error) { ElMessage.error('上传失败') } finally { uploading.value = false }
}

const triggerUpload = () => { document.querySelector('.el-upload').click() }

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm(`确定要删除文档 "${row.filename}" 吗？删除后知识库中的相关内容也会被移除。`, '删除确认', { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' })
    await deleteDocument(row.id); ElMessage.success('文档已删除，知识库已更新'); await loadDocuments()
  } catch (error) { if (error !== 'cancel') ElMessage.error('删除失败') }
}

const handleMenuSelect = (index) => { router.push(index) }
const formatFileSize = (bytes) => { if (bytes < 1024) return bytes + ' B'; if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'; return (bytes / (1024 * 1024)).toFixed(1) + ' MB' }
const getFileIconColor = (type) => { if (type === '.pdf') return '#f56c6c'; if (type === '.docx' || type === '.doc') return '#409eff'; return '#909399' }
const getStatusType = (status) => { const m = { ready: 'success', pending: 'warning', processing: 'info', error: 'danger' }; return m[status] || 'info' }
const getStatusText = (status) => { const m = { ready: '已就绪', pending: '等待中', processing: '处理中', error: '错误' }; return m[status] || status }
const formatDate = (dateStr) => { if (!dateStr) return '-'; return new Date(dateStr).toLocaleString('zh-CN') }
</script>

<style scoped>
.documents-container { display: flex; height: 100vh; background: #f5f5f5; }
.sidebar { width: 240px; background: #2c3e50; color: white; display: flex; flex-direction: column; padding: 16px; }
.new-chat-btn { margin-bottom: 20px; } .new-chat-btn .el-button { width: 100%; }
.sidebar-menu { flex: 1; background: transparent; border: none; } .sidebar-menu .el-menu-item { color: #b0bec5; } .sidebar-menu .el-menu-item.is-active { color: white; background: #34495e; }
.main-area { flex: 1; display: flex; flex-direction: column; padding: 24px; overflow: auto; }
.docs-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.docs-header h2 { font-size: 20px; color: #333; }
.upload-progress { margin-bottom: 16px; }
.docs-list { background: white; border-radius: 8px; padding: 16px; }
.filename-cell { display: flex; align-items: center; gap: 8px; }
.empty-docs { padding: 60px 0; }
</style>
