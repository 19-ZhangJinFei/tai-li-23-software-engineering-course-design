import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { api } from '../api/client'

export interface User { id: string; email: string; display_name: string; role: 'admin' | 'student'; status: string }

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(JSON.parse(localStorage.getItem('user') || 'null'))
  const loggedIn = computed(() => !!localStorage.getItem('access_token'))
  const isAdmin = computed(() => user.value?.role === 'admin')

  function save(data: any) {
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    localStorage.setItem('user', JSON.stringify(data.user))
    user.value = data.user
  }
  async function login(email: string, password: string) {
    const { data } = await api.post('/auth/login', { email, password }); save(data.data)
  }
  async function register(payload: { email: string; display_name: string; password: string }) {
    return (await api.post('/auth/register', payload)).data
  }
  async function fetchMe() {
    const { data } = await api.get('/auth/me'); user.value = data.data
    localStorage.setItem('user', JSON.stringify(data.data))
  }
  async function logout() {
    try { await api.post('/auth/logout', { refresh_token: localStorage.getItem('refresh_token') }) } catch {}
    localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user')
    user.value = null
  }
  return { user, loggedIn, isAdmin, login, register, fetchMe, logout }
})

