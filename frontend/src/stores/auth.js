import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '../api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)

  const isAuthenticated = ref(!!token.value)

  const login = async (username, password) => {
    try {
      const response = await api.post('/auth/login', { username, password })
      token.value = response.data.access_token
      localStorage.setItem('token', token.value)
      isAuthenticated.value = true
      
      // 获取用户信息
      await fetchUser()
      return { success: true }
    } catch (error) {
      return { success: false, message: error.response?.data?.detail || '登录失败' }
    }
  }

  const fetchUser = async () => {
    try {
      const response = await api.get('/auth/me')
      user.value = response.data
    } catch (error) {
      console.error('获取用户信息失败', error)
    }
  }

  const logout = () => {
    token.value = ''
    user.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
  }

  // 初始化时获取用户信息
  if (token.value) {
    fetchUser()
  }

  return {
    token,
    user,
    isAuthenticated,
    login,
    logout,
    fetchUser
  }
})
