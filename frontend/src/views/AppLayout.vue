<script setup lang="ts">
import { useRouter } from 'vue-router'; import { House, Reading, DataAnalysis, SwitchButton } from '@element-plus/icons-vue'; import { useAuthStore } from '../stores/auth'
const auth=useAuthStore(),router=useRouter()
async function logout(){await auth.logout();router.push('/login')}
</script>
<template><div class="app-shell"><aside class="side"><div class="brand"><span class="brand-mark">知</span><span>知课 AI</span></div><nav><router-link class="nav-link" to="/"><el-icon><House/></el-icon><span>学习首页</span></router-link><router-link v-if="auth.isAdmin" class="nav-link" to="/admin"><el-icon><DataAnalysis/></el-icon><span>管理控制台</span></router-link></nav><div class="side-user"><strong>{{auth.user?.display_name}}</strong><span>{{auth.isAdmin?'系统管理员':'学生用户'}}</span><div style="margin-top:10px;cursor:pointer" @click="logout"><el-icon><SwitchButton/></el-icon> 退出登录</div></div></aside><main class="main"><header class="topbar"><div><strong>高校课程知识库智能问答系统</strong></div><el-tag effect="light">{{auth.isAdmin?'管理模式':'学习模式'}}</el-tag></header><router-view/></main></div></template>

