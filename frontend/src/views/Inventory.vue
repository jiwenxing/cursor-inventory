<template>
  <div>
    <div class="header">
      <h2>库存管理</h2>
      <el-button type="primary" @click="handleIn">入库</el-button>
    </div>
    
    <el-tabs v-model="activeTab">
      <el-tab-pane label="库存汇总" name="summary">
        <el-table :data="summary" style="width: 100%" v-loading="loading">
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="product_model" label="型号" />
          <el-table-column prop="current_stock" label="当前库存">
            <template #default="{ row }">
              <span :style="{ color: row.current_stock < 0 ? 'red' : 'inherit' }">
                {{ row.current_stock }}
              </span>
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
      
      <el-tab-pane label="库存流水" name="records">
        <el-table :data="records" style="width: 100%" v-loading="loading">
          <el-table-column prop="product_name" label="商品名称" />
          <el-table-column prop="product_model" label="型号" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'IN' ? 'success' : 'danger'">
                {{ row.type === 'IN' ? '入库' : '出库' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <el-dialog v-model="inDialogVisible" title="入库" width="500px">
      <el-form :model="inForm" :rules="inRules" ref="inFormRef" label-width="100px">
        <el-form-item label="商品" prop="product_id">
          <el-select v-model="inForm.product_id" filterable style="width: 100%">
            <el-option
              v-for="product in products"
              :key="product.id"
              :label="`${product.name} (${product.model})`"
              :value="product.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="数量" prop="quantity">
          <el-input-number v-model="inForm.quantity" :min="0.01" :precision="2" style="width: 100%" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleInSubmit">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '../api'
import dayjs from 'dayjs'

const summary = ref([])
const records = ref([])
const products = ref([])
const loading = ref(false)
const activeTab = ref('summary')
const inDialogVisible = ref(false)
const inFormRef = ref(null)

const inForm = reactive({
  product_id: null,
  quantity: 1
})

const inRules = {
  product_id: [{ required: true, message: '请选择商品', trigger: 'change' }],
  quantity: [{ required: true, message: '请输入数量', trigger: 'blur' }]
}

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const loadSummary = async () => {
  loading.value = true
  try {
    const response = await api.get('/inventory/summary')
    summary.value = response.data
  } catch (error) {
    ElMessage.error('加载库存汇总失败')
  } finally {
    loading.value = false
  }
}

const loadRecords = async () => {
  loading.value = true
  try {
    const response = await api.get('/inventory/records')
    records.value = response.data
  } catch (error) {
    ElMessage.error('加载库存流水失败')
  } finally {
    loading.value = false
  }
}

const loadProducts = async () => {
  try {
    const response = await api.get('/products/')
    products.value = response.data
  } catch (error) {
    console.error('加载商品列表失败', error)
  }
}

const handleIn = () => {
  Object.assign(inForm, { product_id: null, quantity: 1 })
  inDialogVisible.value = true
}

const handleInSubmit = async () => {
  await inFormRef.value.validate(async (valid) => {
    if (valid) {
      try {
        await api.post('/inventory/in', {
          product_id: inForm.product_id,
          type: 'IN',
          quantity: inForm.quantity
        })
        ElMessage.success('入库成功')
        inDialogVisible.value = false
        loadSummary()
        if (activeTab.value === 'records') {
          loadRecords()
        }
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '入库失败')
      }
    }
  })
}

watch(activeTab, (newTab) => {
  if (newTab === 'records' && records.value.length === 0) {
    loadRecords()
  }
})

onMounted(() => {
  loadSummary()
  loadProducts()
})
</script>

<style scoped>
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
