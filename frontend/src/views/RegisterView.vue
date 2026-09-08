<script setup lang="ts">
import { reactive, ref } from 'vue'; import { useRouter } from 'vue-router'; import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'; import { errorMessage } from '../api/client'
const router=useRouter(),auth=useAuthStore(),loading=ref(false)
const form=reactive({display_name:'',email:'',password:''})
async function submit(){loading.value=true;try{await auth.register(form);ElMessage.success('注册成功，请登录');router.push('/login')}catch(e){ElMessage.error(errorMessage(e))}finally{loading.value=false}}
</script>
<template><div class="auth-page"><section class="auth-hero"><div class="eyebrow" style="color:#bdd3ff">加入学习空间</div><h1>从资料阅读<br>走向主动学习</h1><p>在课程知识库中提问、核对来源、生成复习摘要并完成智能测验。</p></section><section class="auth-panel"><div class="auth-card"><div class="eyebrow">创建账号</div><h2>注册学生账号</h2><p class="muted">开发环境会自动通过审核</p><el-form label-position="top" @submit.prevent="submit"><el-form-item label="姓名"><el-input v-model="form.display_name" size="large" /></el-form-item><el-form-item label="邮箱"><el-input v-model="form.email" size="large" /></el-form-item><el-form-item label="密码"><el-input v-model="form.password" type="password" show-password size="large" placeholder="至少 8 位" /></el-form-item><el-button type="primary" :loading="loading" @click="submit">创建账号</el-button></el-form><div style="text-align:center;margin-top:18px" class="muted">已有账号？ <router-link to="/login" style="color:var(--brand)">返回登录</router-link></div></div></section></div></template>

