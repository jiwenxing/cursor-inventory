<template>
  <div>
    <h2>首页</h2>
    <el-row :gutter="20" style="margin-top: 20px">
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalCustomers }}</div>
            <div class="stat-label">客户总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalProducts }}</div>
            <div class="stat-label">商品总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalOrders }}</div>
            <div class="stat-label">订单总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card>
          <div class="stat-item">
            <div class="stat-value">{{ stats.totalReceivables }}</div>
            <div class="stat-label">应收款总额</div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../api'

const stats = ref({
  totalCustomers: 0,
  totalProducts: 0,
  totalOrders: 0,
  totalReceivables: 0
})

const loadStats = async () => {
  try {
    // 商品API已改为分页格式，返回 {items: [], total: number}
    const [customers, products, orders, receivables] = await Promise.all([
      api.get('/customers/'),
      api.get('/products/', { params: { limit: 1 } }),  // 只获取一条，total在response.data.total中
      api.get('/sales-orders/'),
      api.get('/statistics/receivables')
    ])

    // 客户API返回分页格式，取total
    const customerCount = customers.data.total || 0
    // 商品API返回分页格式，取total
    const productCount = products.data.total || 0
    // 订单API返回分页格式，取total
    const orderCount = orders.data.total || 0

    stats.value = {
      totalCustomers: customerCount,
      totalProducts: productCount,
      totalOrders: orderCount,
      totalReceivables: receivables.data.reduce((sum, item) => sum + item.receivable_amount, 0).toFixed(2)
    }
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.stat-item {
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 10px;
}

.stat-label {
  font-size: 14px;
  color: #909399;
}
</style>