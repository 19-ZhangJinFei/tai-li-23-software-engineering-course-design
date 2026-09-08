<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Reading, Connection, DocumentChecked } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import { errorMessage } from '../api/client'

const router = useRouter(), auth = useAuthStore(), loading = ref(false)
const form = reactive({ email: 'student@demo.com', password: 'Student@123456' })
async function submit() { loading.value=true; try { await auth.login(form.email,form.password); router.push('/') } catch(e){ElMessage.error(errorMessage(e))} finally{loading.value=false} }
function useAdmin(){form.email='admin@demo.com';form.password='Admin@123456'}
</script>
<template><div class="auth-page">
  <section class="auth-hero"><div class="eyebrow" style="color:#bdd3ff">COURSE KNOWLEDGE AI</div><h1>让每一份课程资料<br>都能回答问题</h1><p>将讲义、实验指导书与学习笔记构建成可检索、可引用、可验证的课程知识库。</p>
    <div class="auth-feature"><span class="auth-dot"><el-icon><Reading/></el-icon></span><span>基于课程原文的可溯源回答</span></div>
    <div class="auth-feature"><span class="auth-dot"><el-icon><Connection/></el-icon></span><span>RAG 检索增强生成与拒答机制</span></div>
    <div class="auth-feature"><span class="auth-dot"><el-icon><DocumentChecked/></el-icon></span><span>摘要、知识点与智能测验一体化</span></div>
  </section>
  <section class="auth-panel"><div class="auth-card"><div class="eyebrow">欢迎回来</div><h2>登录知课 AI</h2><p class="muted">继续你的课程知识探索</p>
    <el-form label-position="top" @submit.prevent="submit"><el-form-item label="邮箱"><el-input v-model="form.email" size="large" /></el-form-item><el-form-item label="密码"><el-input v-model="form.password" type="password" show-password size="large" @keyup.enter="submit" /></el-form-item><el-button type="primary" :loading="loading" @click="submit">登录</el-button></el-form>
    <div style="text-align:center;margin-top:18px" class="muted">还没有账号？ <router-link to="/register" style="color:var(--brand)">立即注册</router-link></div>
    <div class="demo-box"><strong>演示账号</strong><br>学生：student@demo.com / Student@123456<br><a @click="useAdmin" style="color:var(--brand);cursor:pointer">切换到管理员账号</a></div>
  </div></section>
</div></template>

