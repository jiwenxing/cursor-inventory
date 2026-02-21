<template>
  <el-container>
    <el-header v-if="isLoggedIn">
      <div class="header-content">
        <h2>进销存系统</h2>
        <div class="user-info">
          <span>{{ currentUser?.name || currentUser?.username }}</span>
          <el-button type="danger" size="small" @click="logout">退出</el-button>
        </div>
      </div>
    </el-header>
    <el-container>
      <el-aside v-if="isLoggedIn" width="200px">
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
  </el-container>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from './stores/auth'
import { DataBoard, User, Box, Document, Goods, DataAnalysis, Upload } from '@element-plus/icons-vue'

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
.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  color: white;
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
}

.el-aside {
  background-color: #545c64;
}

.el-main {
  background-color: #f0f2f5;
  padding: 20px;
}
</style>
