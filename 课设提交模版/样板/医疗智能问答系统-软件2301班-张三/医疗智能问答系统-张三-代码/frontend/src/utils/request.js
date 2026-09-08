import axios from 'axios'
import { ElMessage } from 'element-plus'

const request = axios.create({ baseURL: '/api', timeout: 30000 })

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) { config.headers.Authorization = `Bearer ${token}` }
  return config
}, (error) => Promise.reject(error))

request.interceptors.response.use((response) => response.data, (error) => {
  if (error.response) {
    const status = error.response.status
    const detail = error.response.data?.detail || '未知错误'
    switch (status) {
      case 401: ElMessage.error('登录已过期，请重新登录'); localStorage.removeItem('access_token'); window.location.href = '/login'; break
      case 403: ElMessage.error('没有权限访问'); break
      case 404: ElMessage.error('请求的资源不存在'); break
      case 500: ElMessage.error('服务器内部错误'); break
      default: ElMessage.error(detail)
    }
  } else if (error.code === 'ECONNABORTED') { ElMessage.error('请求超时，请稍后重试') }
  else { ElMessage.error('网络错误，请检查网络连接') }
  return Promise.reject(error)
})

export default request
