import axios from 'axios'

export interface ApiEnvelope<T> { data: T; message: string; request_id: string; code?: string }

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || (import.meta.env.DEV ? '/api/v1' : '/server/api/v1'),
  timeout: 120000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original?._retried && localStorage.getItem('refresh_token')) {
      original._retried = true
      try {
        const { data } = await axios.post<ApiEnvelope<any>>(`${api.defaults.baseURL}/auth/refresh`, {
          refresh_token: localStorage.getItem('refresh_token'),
        })
        localStorage.setItem('access_token', data.data.access_token)
        localStorage.setItem('refresh_token', data.data.refresh_token)
        original.headers.Authorization = `Bearer ${data.data.access_token}`
        return api(original)
      } catch { localStorage.clear(); location.href = '/login' }
    }
    return Promise.reject(error)
  },
)

export function errorMessage(error: any): string {
  return error?.response?.data?.message || error?.message || '操作失败，请稍后重试'
}
