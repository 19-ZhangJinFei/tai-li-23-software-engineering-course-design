import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue'),
    meta: { title: '登录 - 医疗智能问答系统' } },
  { path: '/chat', name: 'Chat', component: () => import('../views/Chat.vue'),
    meta: { title: '智能问答 - 医疗智能问答系统', requiresAuth: true } },
  { path: '/documents', name: 'Documents', component: () => import('../views/Documents.vue'),
    meta: { title: '知识库管理 - 医疗智能问答系统', requiresAuth: true } },
  { path: '/', redirect: '/chat' }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  document.title = to.meta.title || '医疗智能问答系统'
  if (to.meta.requiresAuth) {
    const token = localStorage.getItem('access_token')
    if (!token) { next('/login'); return }
  }
  next()
})

export default router
