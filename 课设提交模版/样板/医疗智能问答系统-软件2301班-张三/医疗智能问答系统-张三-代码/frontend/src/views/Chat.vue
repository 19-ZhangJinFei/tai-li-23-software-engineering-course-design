<template>
  <div class="chat-container">
    <div class="sidebar">
      <div class="new-chat-btn"><el-button type="primary" @click="handleNewSession" :icon="Plus" round>新建对话</el-button></div>
      <el-menu :default-active="activeRoute" class="sidebar-menu" @select="handleMenuSelect">
        <el-menu-item index="/chat"><el-icon><ChatDotRound /></el-icon><span>智能问答</span></el-menu-item>
        <el-menu-item index="/documents"><el-icon><Document /></el-icon><span>知识库管理</span></el-menu-item>
      </el-menu>
      <div class="user-info">
        <el-dropdown>
          <span class="user-dropdown"><el-avatar :size="32">{{ currentUser?.username?.charAt(0).toUpperCase() }}</el-avatar><span>{{ currentUser?.username }}</span></span>
          <template #dropdown><el-dropdown-menu><el-dropdown-item @click="handleLogout">退出登录</el-dropdown-item></el-dropdown-menu></template>
        </el-dropdown>
      </div>
    </div>
    <div class="main-area">
      <div class="chat-header"><h2>医疗智能问答</h2><span v-if="sessionId" class="session-info">会话: {{ sessionId.substring(0, 8) }}...</span></div>
      <div class="messages-container" ref="messagesContainer">
        <div v-if="messages.length === 0" class="empty-state"><el-empty description="开始提问吧！例如：阿司匹林的副作用是什么？" /></div>
        <div v-for="(msg, index) in messages" :key="index" :class="['message-item', msg.role === 'user' ? 'user-message' : 'assistant-message']">
          <div class="message-avatar"><el-avatar :size="36" :style="{ background: msg.role === 'user' ? '#409eff' : '#67c23a' }">{{ msg.role === 'user' ? '我' : 'AI' }}</el-avatar></div>
          <div class="message-content">
            <div class="message-text">{{ msg.content }}</div>
            <div v-if="msg.sources && msg.sources.length > 0" class="message-sources">
              <div class="sources-title">📚 回答来源：</div>
              <div v-for="(source, sIdx) in msg.sources" :key="sIdx" class="source-item"><el-tag size="small" type="info">{{ source.filename }}</el-tag><span class="source-text">{{ source.text }}</span></div>
            </div>
          </div>
        </div>
        <div v-if="loading" class="message-item assistant-message">
          <div class="message-avatar"><el-avatar :size="36" style="background: #67c23a">AI</el-avatar></div>
          <div class="message-content"><div class="loading-dots"><span></span><span></span><span></span></div></div>
        </div>
      </div>
      <div class="input-area">
        <el-input v-model="inputMessage" type="textarea" :rows="2" placeholder="请输入您的问题..." @keyup.enter.native="handleSend" :disabled="loading" />
        <el-button type="primary" @click="handleSend" :loading="loading" :disabled="!inputMessage.trim()">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, ChatDotRound, Document } from '@element-plus/icons-vue'
import { sendMessage, getCurrentUser, getSessions } from '../api'

const router = useRouter()
const messages = ref([])
const inputMessage = ref('')
const loading = ref(false)
const sessionId = ref(null)
const sessions = ref([])
const currentUser = ref(null)
const activeRoute = ref('/chat')
const messagesContainer = ref()

onMounted(async () => {
  const token = localStorage.getItem('access_token')
  if (!token) { router.push('/login'); return }
  try { currentUser.value = await getCurrentUser() } catch (error) { router.push('/login'); return }
  try { const res = await getSessions(); sessions.value = res.sessions || [] } catch (error) { console.error('获取会话列表失败:', error) }
})

const handleSend = async () => {
  const message = inputMessage.value.trim()
  if (!message || loading.value) return
  messages.value.push({ role: 'user', content: message })
  inputMessage.value = ''
  loading.value = true
  await scrollToBottom()
  try {
    const res = await sendMessage(message, sessionId.value)
    if (res.session_id) sessionId.value = res.session_id
    messages.value.push({ role: 'assistant', content: res.answer, sources: res.sources || [] })
  } catch (error) {
    messages.value.push({ role: 'assistant', content: '抱歉，回答问题时出现了错误，请稍后重试。' })
  } finally { loading.value = false; await scrollToBottom() }
}

const handleNewSession = () => { messages.value = []; sessionId.value = null; ElMessage.success('已创建新对话') }
const handleMenuSelect = (index) => { router.push(index) }
const handleLogout = async () => {
  try { await ElMessageBox.confirm('确定要退出登录吗？', '提示', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }); localStorage.removeItem('access_token'); ElMessage.success('已退出登录'); router.push('/login') } catch (error) {}
}
const scrollToBottom = async () => { await nextTick(); if (messagesContainer.value) messagesContainer.value.scrollTop = messagesContainer.value.scrollHeight }
</script>

<style scoped>
.chat-container { display: flex; height: 100vh; background: #f5f5f5; }
.sidebar { width: 240px; background: #2c3e50; color: white; display: flex; flex-direction: column; padding: 16px; }
.new-chat-btn { margin-bottom: 20px; } .new-chat-btn .el-button { width: 100%; }
.sidebar-menu { flex: 1; background: transparent; border: none; }
.sidebar-menu .el-menu-item { color: #b0bec5; } .sidebar-menu .el-menu-item.is-active { color: white; background: #34495e; }
.user-info { padding-top: 16px; border-top: 1px solid #3e556d; }
.user-dropdown { display: flex; align-items: center; gap: 8px; cursor: pointer; color: white; }
.main-area { flex: 1; display: flex; flex-direction: column; }
.chat-header { padding: 16px 24px; background: white; border-bottom: 1px solid #e0e0e0; display: flex; justify-content: space-between; align-items: center; }
.chat-header h2 { font-size: 18px; color: #333; }
.session-info { font-size: 12px; color: #999; }
.messages-container { flex: 1; overflow-y: auto; padding: 20px; }
.empty-state { display: flex; justify-content: center; align-items: center; height: 100%; }
.message-item { display: flex; gap: 12px; margin-bottom: 20px; max-width: 80%; }
.user-message { flex-direction: row-reverse; margin-left: auto; }
.message-text { padding: 12px 16px; border-radius: 12px; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }
.user-message .message-text { background: #409eff; color: white; }
.assistant-message .message-text { background: white; color: #333; }
.message-sources { margin-top: 8px; padding: 8px 12px; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #67c23a; }
.sources-title { font-size: 12px; color: #67c23a; font-weight: bold; margin-bottom: 4px; }
.source-item { font-size: 12px; color: #666; margin-top: 4px; }
.loading-dots { display: flex; gap: 4px; padding: 12px 16px; background: white; border-radius: 12px; }
.loading-dots span { width: 8px; height: 8px; border-radius: 50%; background: #999; animation: bounce 1.4s infinite ease-in-out; }
.loading-dots span:nth-child(2) { animation-delay: 0.2s; } .loading-dots span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }
.input-area { padding: 16px 24px; background: white; border-top: 1px solid #e0e0e0; display: flex; gap: 12px; align-items: flex-end; }
.input-area .el-textarea { flex: 1; }
</style>
