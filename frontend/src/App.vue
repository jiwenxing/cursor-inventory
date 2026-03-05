<template>
  <el-container class="app-container">
    <el-header v-if="isLoggedIn">
      <div class="header-content">
        <h2>杭州松德机械科技有限公司</h2>
        <div class="user-info">
          <span>{{ currentUser?.name || currentUser?.username }}</span>
          <el-button type="danger" size="small" @click="logout">退出</el-button>
        </div>
      </div>
    </el-header>
    <el-container v-if="isLoggedIn" class="main-container">
      <el-aside width="200px">
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#ffd04b"
        >
          <el-menu-item index="/dashboard">
            <el-icon><DataBoard /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/customers">
            <el-icon><User /></el-icon>
            <span>客户管理</span>
          </el-menu-item>
          <el-menu-item index="/suppliers">
            <el-icon><Shop /></el-icon>
            <span>供应商管理</span>
          </el-menu-item>
          <el-menu-item index="/products">
            <el-icon><Box /></el-icon>
            <span>商品管理</span>
          </el-menu-item>
          <el-menu-item index="/sales-orders">
            <el-icon><Document /></el-icon>
            <span>销售订单</span>
          </el-menu-item>
          <el-menu-item index="/inventory">
            <el-icon><Goods /></el-icon>
            <span>库存管理</span>
          </el-menu-item>
          <el-menu-item index="/statistics">
            <el-icon><DataAnalysis /></el-icon>
            <span>统计报表</span>
          </el-menu-item>
          <el-menu-item index="/import">
            <el-icon><Upload /></el-icon>
            <span>Excel导入</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main>
        <router-view />
      </el-main>
    </el-container>
    <el-main v-else class="login-main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { DataBoard, User, Shop, Box, Document, Goods, DataAnalysis, Upload } from '@element-plus/icons-vue'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const isLoggedIn = computed(() => authStore.isAuthenticated)
const currentUser = computed(() => authStore.user)
const activeMenu = computed(() => route.path)

const logout = () => {
  authStore.logout()
  router.push('/login')
}

onMounted(() => {
  if (!isLoggedIn.value && route.path !== '/login') {
    router.push('/login')
  }
})
</script>

<style scoped>
.app-container {
  height: 100vh;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  color: white;
}

.header-content h2 {
  margin: 0;
  font-size: 22px;
  font-weight: 600;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 10px;
}

.el-header {
  background-color: #409eff;
  color: white;
  line-height: 60px;
  padding: 0 20px;
}

.main-container {
  height: calc(100vh - 60px);
}

.el-aside {
  background-color: #545c64;
}

.el-main {
  background-color: #f0f2f5;
  padding: 15px;
  overflow: auto;
}

.login-main {
  background-color: #f0f2f5;
  display: flex;
  justify-content: center;
  align-items: center;
}
</style>