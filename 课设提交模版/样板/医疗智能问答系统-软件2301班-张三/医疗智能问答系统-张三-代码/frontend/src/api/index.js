import request from '../utils/request'

export function register(data) { return request({ url: '/auth/register', method: 'post', data }) }
export function login(data) { return request({ url: '/auth/login', method: 'post', data }) }
export function getCurrentUser() { return request({ url: '/auth/me', method: 'get' }) }
export function uploadDocument(file) {
  const formData = new FormData(); formData.append('file', file)
  return request({ url: '/documents/upload', method: 'post', data: formData, headers: { 'Content-Type': 'multipart/form-data' } })
}
export function getDocuments() { return request({ url: '/documents/', method: 'get' }) }
export function deleteDocument(docId) { return request({ url: `/documents/${docId}`, method: 'delete' }) }
export function sendMessage(message, sessionId) { return request({ url: '/chat/', method: 'post', data: { message, session_id: sessionId } }) }
export function createSession() { return request({ url: '/chat/session', method: 'post' }) }
export function getChatHistory(sessionId) { return request({ url: `/chat/history/${sessionId}`, method: 'get' }) }
export function clearChatHistory(sessionId) { return request({ url: `/chat/history/${sessionId}`, method: 'delete' }) }
export function getChatStatus() { return request({ url: '/chat/status', method: 'get' }) }
export function getSessions() { return request({ url: '/chat/sessions', method: 'get' }) }
