import { createRouter, createWebHistory } from 'vue-router'
import LoginView from './views/LoginView.vue'
import RegisterView from './views/RegisterView.vue'
import AppLayout from './views/AppLayout.vue'
import DashboardView from './views/DashboardView.vue'
import CourseView from './views/CourseView.vue'
import AdminView from './views/AdminView.vue'

const router = createRouter({ history: createWebHistory(), routes: [
  { path: '/login', component: LoginView, meta: { public: true } },
  { path: '/register', component: RegisterView, meta: { public: true } },
  { path: '/', component: AppLayout, children: [
    { path: '', component: DashboardView },
    { path: 'courses/:id', component: CourseView },
    { path: 'admin', component: AdminView },
  ] },
] })

router.beforeEach((to) => {
  if (!to.meta.public && !localStorage.getItem('access_token')) return '/login'
  if (to.meta.public && localStorage.getItem('access_token')) return '/'
})

export default router

