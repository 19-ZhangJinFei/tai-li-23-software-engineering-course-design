<template>
  <div class="login-container">
    <div class="login-box">
      <h1 class="title">医疗智能问答系统</h1>
      <p class="subtitle">基于RAG的医疗领域知识问答平台</p>
      <el-tabs v-model="activeTab" class="login-tabs">
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" :rules="loginRules" ref="loginFormRef">
            <el-form-item prop="username">
              <el-input v-model="loginForm.username" placeholder="请输入用户名" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="loginForm.password" type="password" placeholder="请输入密码" :prefix-icon="Lock" size="large" show-password @keyup.enter="handleLogin" />
            </el-form-item>
            <el-button type="primary" size="large" :loading="loading" @click="handleLogin" class="login-btn">登录</el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form :model="registerForm" :rules="registerRules" ref="registerFormRef">
            <el-form-item prop="username">
              <el-input v-model="registerForm.username" placeholder="请输入用户名（3-20字符）" :prefix-icon="User" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="registerForm.password" type="password" placeholder="请输入密码（6-50字符）" :prefix-icon="Lock" size="large" show-password />
            </el-form-item>
            <el-form-item prop="confirmPassword">
              <el-input v-model="registerForm.confirmPassword" type="password" placeholder="请再次输入密码" :prefix-icon="Lock" size="large" show-password @keyup.enter="handleRegister" />
            </el-form-item>
            <el-button type="primary" size="large" :loading="loading" @click="handleRegister" class="login-btn">注册</el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock } from '@element-plus/icons-vue'
import { login, register } from '../api'

const router = useRouter()
const activeTab = ref('login')
const loading = ref(false)
const loginFormRef = ref()
const registerFormRef = ref()

const loginForm = reactive({ username: '', password: '' })
const registerForm = reactive({ username: '', password: '', confirmPassword: '' })

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}
const registerRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }, { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }, { min: 6, max: 50, message: '密码长度为6-50个字符', trigger: 'blur' }],
  confirmPassword: [{ required: true, message: '请再次输入密码', trigger: 'blur' }, { validator: (rule, value, callback) => { value !== registerForm.password ? callback(new Error('两次输入的密码不一致')) : callback() }, trigger: 'blur' }]
}

const handleLogin = async () => {
  try {
    await loginFormRef.value.validate()
    loading.value = true
    const res = await login(loginForm)
    localStorage.setItem('access_token', res.access_token)
    ElMessage.success('登录成功')
    router.push('/chat')
  } catch (error) {
    if (error.response) ElMessage.error(error.response.data?.detail || '登录失败')
  } finally { loading.value = false }
}

const handleRegister = async () => {
  try {
    await registerFormRef.value.validate()
    loading.value = true
    await register({ username: registerForm.username, password: registerForm.password })
    ElMessage.success('注册成功，请登录')
    activeTab.value = 'login'
    loginForm.username = registerForm.username
    loginForm.password = registerForm.password
  } catch (error) {
    if (error.response) ElMessage.error(error.response.data?.detail || '注册失败')
  } finally { loading.value = false }
}
</script>

<style scoped>
.login-container { display: flex; justify-content: center; align-items: center; min-height: 100vh; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); }
.login-box { width: 400px; padding: 40px; background: white; border-radius: 12px; box-shadow: 0 20px 60px rgba(0,0,0,0.3); }
.title { text-align: center; font-size: 24px; color: #333; margin-bottom: 8px; }
.subtitle { text-align: center; font-size: 14px; color: #999; margin-bottom: 30px; }
.login-btn { width: 100%; margin-top: 10px; }
</style>
