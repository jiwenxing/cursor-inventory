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
          <el-table-column prop="product_brand" label="品牌" width="100" />
          <el-table-column prop="supplier_name" label="供应商" width="150" />
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
          <el-table-column prop="product_model" label="型号" width="100" />
          <el-table-column prop="product_brand" label="品牌" width="100" />
          <el-table-column prop="supplier_name" label="供应商" width="120" />
          <el-table-column prop="type" label="类型" width="100">
            <template #default="{ row }">
              <el-tag :type="row.type === 'IN' ? 'success' : 'danger'">
                {{ row.type === 'IN' ? '入库' : '出库' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column prop="related_order_type" label="关联类型" width="100">
            <template #default="{ row }">
              <span v-if="row.related_order_type === 'purchase'">采购订单</span>
              <span v-else-if="row.related_order_type === 'sales'">销售订单</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="related_order_id" label="关联订单" width="100">
            <template #default="{ row }">
              <span v-if="row.related_order_id">{{ row.related_order_id }}</span>
              <span v-else>-</span>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </el-tab-pane>
    </el-tabs>

    <!-- 入库对话框 -->
    <el-dialog v-model="inDialogVisible" title="入库" width="900px">
      <el-form :model="inForm" :rules="inRules" ref="inFormRef" label-width="100px">
        <!-- 方式一：选择采购订单入库 -->
        <el-form-item label="采购订单">
          <el-select
            v-model="selectedPurchaseOrderId"
            filterable
            placeholder="选择采购订单（可选）"
            style="width: 100%"
            @change="handlePurchaseOrderSelect"
            clearable
          >
            <el-option
              v-for="order in pendingPurchaseOrders"
              :key="order.order_id"
              :label="`订单 ${order.order_id} - ${order.supplier_name} (${order.status})`"
              :value="order.order_id"
            />
          </el-select>
        </el-form-item>

        <!-- 待入库商品列表（选择采购订单后显示） -->
        <div v-if="selectedPurchaseOrder" style="margin-bottom: 20px;">
          <el-divider content-position="left">待入库商品</el-divider>
          <el-table :data="pendingReceiveItems" border max-height="300">
            <el-table-column prop="product_name" label="商品名称" />
            <el-table-column prop="product_model" label="型号" width="100" />
            <el-table-column prop="quantity" label="订单数量" width="80" />
            <el-table-column prop="received_quantity" label="已入库" width="80" />
            <el-table-column prop="unreceived_quantity" label="待入库" width="80">
              <template #default="{ row }">
                <span style="color: #67c23a; font-weight: bold;">{{ row.unreceived_quantity }}</span>
              </template>
            </el-table-column>
            <el-table-column label="本次入库" width="120">
              <template #default="{ row, $index }">
                <el-input-number
                  v-model="row.receive_quantity"
                  :min="1"
                  :max="row.unreceived_quantity"
                  :precision="0"
                  size="small"
                  controls-position="right"
                  style="width: 100%"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button
                  size="small"
                  type="primary"
                  @click="submitReceiveItem($index)"
                  :disabled="!pendingReceiveItems[$index].receive_quantity"
                >
                  入库
                </el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>

        <!-- 方式二：直接入库（不关联订单） -->
        <el-divider>或直接入库</el-divider>
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
        <el-form-item>
          <el-button type="primary" @click="handleDirectInSubmit">直接入库</el-button>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="inDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, watch, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import dayjs from 'dayjs'

const summary = ref([])
const records = ref([])
const products = ref([])
const loading = ref(false)
const activeTab = ref('summary')
const inDialogVisible = ref(false)
const inFormRef = ref(null)

const selectedPurchaseOrderId = ref(null)
const selectedPurchaseOrder = ref(null)
const pendingPurchaseOrders = ref([])
const pendingReceiveItems = ref([])

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
    const response = await api.get('/products/', { params: { limit: 1000 } })
    products.value = response.data.items || response.data
  } catch (error) {
    console.error('加载商品列表失败', error)
  }
}

// 加载待入库的采购订单
const loadPendingPurchaseOrders = async () => {
  try {
    const response = await api.get('/inventory/purchase-orders/pending')
    pendingPurchaseOrders.value = response.data
  } catch (error) {
    console.error('加载待入库订单失败', error)
  }
}

const handleIn = async () => {
  Object.assign(inForm, { product_id: null, quantity: 1 })
  selectedPurchaseOrderId.value = null
  selectedPurchaseOrder.value = null
  pendingReceiveItems.value = []
  await loadPendingPurchaseOrders()
  inDialogVisible.value = true
}

// 选择采购订单
const handlePurchaseOrderSelect = async (orderId) => {
  if (!orderId) {
    selectedPurchaseOrder.value = null
    pendingReceiveItems.value = []
    return
  }

  const order = pendingPurchaseOrders.value.find(o => o.order_id === orderId)
  if (order) {
    selectedPurchaseOrder.value = order
    pendingReceiveItems.value = order.items.map(item => ({
      ...item,
      receive_quantity: item.unreceived_quantity  // 默认全选
    }))
  }
}

// 提交单个商品入库
const submitReceiveItem = async (index) => {
  const item = pendingReceiveItems.value[index]
  if (!item.receive_quantity || item.receive_quantity <= 0) {
    ElMessage.warning('请输入入库数量')
    return
  }

  try {
    await api.post('/inventory/in', {
      product_id: item.product_id,
      type: 'IN',
      quantity: item.receive_quantity
    }, {
      params: {
        purchase_order_id: selectedPurchaseOrder.value.order_id
      }
    })

    ElMessage.success('入库成功')

    // 重新加载订单
    await loadPendingPurchaseOrders()
    handlePurchaseOrderSelect(selectedPurchaseOrderId.value)
    loadSummary()
    if (activeTab.value === 'records') {
      loadRecords()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '入库失败')
  }
}

// 直接入库（不关联订单）
const handleDirectInSubmit = async () => {
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
