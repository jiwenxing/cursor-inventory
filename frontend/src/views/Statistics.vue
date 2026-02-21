<template>
  <div>
    <h2>统计报表</h2>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="按客户统计" name="customer">
        <el-table :data="customerStats" style="width: 100%" v-loading="loading">
          <el-table-column prop="customer_name" label="客户名称" />
          <el-table-column prop="order_count" label="订单数量" />
          <el-table-column prop="total_amount" label="销售总额">
            <template #default="{ row }">
              ¥{{ row.total_amount.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="按商品统计" name="product">
        <el-table :data="productStats" style="width: 100%" v-loading="loading">
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="product_model" label="型号" />
          <el-table-column prop="total_quantity" label="销售数量" />
          <el-table-column prop="total_amount" label="销售总额">
            <template #default="{ row }">
              ¥{{ row.total_amount.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="应收款统计" name="receivables">
        <el-table :data="receivables" style="width: 100%" v-loading="loading">
          <el-table-column prop="customer_name" label="客户名称" />
          <el-table-column prop="receivable_amount" label="应收金额">
            <template #default="{ row }">
              <span style="color: red; font-weight: bold">
                ¥{{ row.receivable_amount.toFixed(2) }}
              </span>
            </template>
          </el-table-column>
        </el-table>
        <div style="margin-top: 20px; text-align: right">
          <strong>应收款总额：¥{{ totalReceivables.toFixed(2) }}</strong>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'

const activeTab = ref('customer')
const loading = ref(false)
const customerStats = ref([])
const productStats = ref([])
const receivables = ref([])

const totalReceivables = computed(() => {
  return receivables.value.reduce((sum, item) => sum + item.receivable_amount, 0)
})

const loadCustomerStats = async () => {
  loading.value = true
  try {
    const response = await api.get('/statistics/sales-by-customer')
    customerStats.value = response.data
  } catch (error) {
    ElMessage.error('加载客户统计失败')
  } finally {
    loading.value = false
  }
}

const loadProductStats = async () => {
  loading.value = true
  try {
    const response = await api.get('/statistics/sales-by-product')
    productStats.value = response.data
  } catch (error) {
    ElMessage.error('加载商品统计失败')
  } finally {
    loading.value = false
  }
}

const loadReceivables = async () => {
  loading.value = true
  try {
    const response = await api.get('/statistics/receivables')
    receivables.value = response.data
  } catch (error) {
    ElMessage.error('加载应收款统计失败')
  } finally {
    loading.value = false
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'product' && productStats.value.length === 0) {
    loadProductStats()
  } else if (newTab === 'receivables' && receivables.value.length === 0) {
    loadReceivables()
  }
})

onMounted(() => {
  loadCustomerStats()
})
</script>
