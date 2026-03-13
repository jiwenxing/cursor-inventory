<template>
  <div class="purchase-orders-container">
    <div class="header">
      <h2>采购订单</h2>
      <el-button type="primary" @click="handleAdd">新增订单</el-button>
    </div>

    <!-- 搜索过滤区域 -->
    <div class="search-box">
      <el-row :gutter="15" style="margin-bottom: 15px;">
        <el-col :span="4">
          <el-select
            v-model="searchForm.supplier_id"
            placeholder="选择供应商"
            filterable
            clearable
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option
              v-for="s in suppliers"
              :key="s.id"
              :label="s.name"
              :value="s.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="searchForm.status"
            placeholder="入库状态"
            clearable
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option label="待入库" value="待入库" />
            <el-option label="部分入库" value="部分入库" />
            <el-option label="已完成" value="已完成" />
          </el-select>
        </el-col>
        <el-col :span="6">
          <el-date-picker
            v-model="searchForm.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            value-format="YYYY-MM-DD"
            :shortcuts="dateShortcuts"
            @change="handleDateRangeChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="2">
          <el-button @click="handleReset" plain>重置</el-button>
        </el-col>
        <el-col :span="3">
          <el-input
            v-model.number="searchForm.min_amount"
            placeholder="最小金额"
            type="number"
            clearable
            @change="handleSearch"
          />
        </el-col>
        <el-col :span="3">
          <el-input
            v-model.number="searchForm.max_amount"
            placeholder="最大金额"
            type="number"
            clearable
            @change="handleSearch"
          />
        </el-col>
      </el-row>
    </div>

    <el-table :data="orders" style="width: 100%; table-layout: fixed;" v-loading="loading" row-key="id">
      <el-table-column type="expand" width="50">
        <template #default="{ row }">
          <div style="padding: 20px;">
            <h4 style="margin-bottom: 15px;">订单明细</h4>
            <el-table :data="row.items" style="width: 100%" :show-header="true" size="small">
              <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
              <el-table-column prop="product_model" label="型号" width="100" />
              <el-table-column prop="quantity" label="数量" width="70" />
              <el-table-column prop="unit_price" label="单价" width="90">
                <template #default="{ row }">
                  ¥{{ row.unit_price?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="received_quantity" label="已入库" width="70" />
              <el-table-column prop="unreceived_quantity" label="未入库" width="70">
                <template #default="{ row }">
                  <span :style="{ color: row.unreceived_quantity > 0 ? '#e6a23c' : '#67c23a' }">
                    {{ row.unreceived_quantity }}
                  </span>
                </template>
              </el-table-column>
              <el-table-column prop="line_total" label="行金额" width="90">
                <template #default="{ row }">
                  ¥{{ row.line_total?.toFixed(2) }}
                </template>
              </el-table-column>
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="订单号" width="100" />
      <el-table-column prop="order_date" label="订单日期" width="160">
        <template #default="{ row }">
          {{ formatDate(row.order_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="supplier_name" label="供应商" show-overflow-tooltip />
      <el-table-column prop="purchaser_name" label="采购员" width="100" />
      <el-table-column prop="total_amount" label="订单金额" width="110">
        <template #default="{ row }">
          ¥{{ row.total_amount?.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="purchase_status" label="采购状态" width="120">
        <template #default="{ row }">
          <el-select
            v-model="row.purchase_status"
            size="small"
            :disabled="row.items?.some(i => i.received_quantity > 0)"
            @change="handlePurchaseStatusChange(row)"
          >
            <el-option label="待下单" value="待下单" />
            <el-option label="待确认" value="待确认" />
            <el-option label="已下单" value="已下单" />
          </el-select>
        </template>
      </el-table-column>
      <el-table-column label="来源订单" width="120">
        <template #default="{ row }">
          <span v-if="row.source_sales_order_id" style="color: #409EFF">
            SO-{{ row.source_sales_order_id }}
          </span>
          <span v-else style="color: #909399">-</span>
        </template>
      </el-table-column>
      <el-table-column prop="status" label="入库状态" width="120">
        <template #default="{ row }">
          <el-tag :type="row.status === '已完成' ? 'success' : row.status === '部分入库' ? 'warning' : 'info'" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleView(row)">查看</el-button>
          <el-button size="small" link type="primary" @click="handleEdit(row)" :disabled="row.status === '已完成'">编辑</el-button>
          <el-button size="small" link type="success" @click="handleReceive(row)" :disabled="row.status === '已完成'">入库</el-button>
          <el-button size="small" link type="danger" @click="handleDelete(row)" :disabled="row.items?.some(i => i.received_quantity > 0) || row.purchase_status === '已下单'">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <div class="pagination-container">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[15, 30, 50, 100]"
        :total="total"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="900px">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="订单日期" prop="order_date">
              <el-date-picker v-model="form.order_date" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="供应商" prop="supplier_id">
              <el-select v-model="form.supplier_id" filterable style="width: 100%">
                <el-option
                  v-for="supplier in suppliers"
                  :key="supplier.id"
                  :label="supplier.name"
                  :value="supplier.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" type="textarea" :rows="2" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>订单明细</el-divider>
        <el-table :data="form.items" border style="width: 100%">
          <el-table-column label="商品" min-width="120" resizable>
            <template #default="{ row, $index }">
              <el-select v-model="row.product_id" filterable placeholder="选择商品" style="width: 100%" @change="handleProductChange($index)">
                <el-option
                  v-for="product in products"
                  :key="product.id"
                  :label="`${product.name} (${product.model})`"
                  :value="product.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="110" align="center">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="1" :step="1" size="small" style="width: 90%" controls-position="right" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120" align="center">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price" :min="0" :precision="2" size="small" controls-position="right" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="行金额" width="120">
            <template #default="{ row }">
              ¥{{ row.line_total?.toFixed(2) || '0.00' }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="80">
            <template #default="{ $index }">
              <el-button size="small" type="danger" @click="removeItem($index)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-button style="margin-top: 10px" @click="addItem">添加商品</el-button>
        <div style="margin-top: 20px; text-align: right">
          <strong>订单总额：¥{{ calculateTotal().toFixed(2) }}</strong>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 入库对话框 -->
    <el-dialog v-model="receiveDialogVisible" title="采购入库" width="800px">
      <div v-if="currentOrder" style="margin-bottom: 15px;">
        <el-descriptions title="采购订单信息" :column="3" border>
          <el-descriptions-item label="订单号">{{ currentOrder.id }}</el-descriptions-item>
          <el-descriptions-item label="供应商">{{ currentOrder.supplier_name }}</el-descriptions-item>
          <el-descriptions-item label="订单日期">{{ formatDate(currentOrder.order_date) }}</el-descriptions-item>
          <el-descriptions-item label="采购状态">
            <el-tag :type="currentOrder.purchase_status === '已下单' ? 'success' : 'info'" size="small">
              {{ currentOrder.purchase_status }}
            </el-tag>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-table :data="receiveItems" style="width: 100%">
        <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
        <el-table-column prop="product_model" label="型号" width="100" />
        <el-table-column prop="quantity" label="采购数量" width="80" />
        <el-table-column prop="received_quantity" label="已入库" width="80" />
        <el-table-column label="未入库" width="80">
          <template #default="{ row }">
            {{ row.quantity - row.received_quantity }}
          </template>
        </el-table-column>
        <el-table-column label="本次入库" width="120">
          <template #default="{ row }">
            <el-input-number
              v-model="row.receive_quantity"
              :min="0"
              :max="row.quantity - row.received_quantity"
              :disabled="currentOrder.purchase_status !== '已下单'"
              size="small"
              controls-position="right"
              style="width: 100%"
            />
          </template>
        </el-table-column>
      </el-table>

      <div style="margin-top: 15px; color: #909399; font-size: 13px;">
        <el-icon><info-filled /></el-icon> 只有采购状态为「已下单」的订单才能入库
      </div>

      <template #footer>
        <el-button @click="receiveDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleConfirmReceive">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import dayjs from 'dayjs'

const orders = ref([])
const suppliers = ref([])
const products = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const receiveDialogVisible = ref(false)
const dialogTitle = ref('新增订单')
const formRef = ref(null)
const editingId = ref(null)
const currentOrder = ref(null)
const receiveItems = ref([])

// 分页相关
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

// 搜索表单
const searchForm = reactive({
  supplier_id: undefined,
  status: '',
  dateRange: [],
  start_date: '',
  end_date: '',
  min_amount: undefined,
  max_amount: undefined
})

const form = reactive({
  order_date: new Date(),
  supplier_id: null,
  source_sales_order_id: null,
  remark: '',
  items: []
})

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 日期选择器快捷选项
const dateShortcuts = [
  {
    text: '今天',
    value: () => {
      const today = dayjs().format('YYYY-MM-DD')
      return [today, today]
    }
  },
  {
    text: '昨天',
    value: () => {
      const yesterday = dayjs().subtract(1, 'day').format('YYYY-MM-DD')
      return [yesterday, yesterday]
    }
  },
  {
    text: '本周',
    value: () => {
      const start = dayjs().startOf('week').add(1, 'day').format('YYYY-MM-DD')
      const end = dayjs().format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '上周',
    value: () => {
      const start = dayjs().startOf('week').subtract(1, 'week').add(1, 'day').format('YYYY-MM-DD')
      const end = dayjs().startOf('week').format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '本月',
    value: () => {
      const start = dayjs().startOf('month').format('YYYY-MM-DD')
      const end = dayjs().format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '上月',
    value: () => {
      const start = dayjs().subtract(1, 'month').startOf('month').format('YYYY-MM-DD')
      const end = dayjs().subtract(1, 'month').endOf('month').format('YYYY-MM-DD')
      return [start, end]
    }
  },
  {
    text: '本年',
    value: () => {
      const start = dayjs().startOf('year').format('YYYY-MM-DD')
      const end = dayjs().format('YYYY-MM-DD')
      return [start, end]
    }
  }
]

// 日期范围变化
const handleDateRangeChange = (val) => {
  if (val && val.length === 2) {
    searchForm.start_date = val[0]
    searchForm.end_date = val[1]
  } else {
    searchForm.start_date = ''
    searchForm.end_date = ''
  }
  handleSearch()
}

// 获取搜索参数
const getSearchParams = () => {
  const params = {}
  if (searchForm.supplier_id !== undefined && searchForm.supplier_id !== '') {
    params.supplier_id = searchForm.supplier_id
  }
  if (searchForm.status) {
    params.status = searchForm.status
  }
  if (searchForm.start_date) {
    params.start_date = searchForm.start_date
  }
  if (searchForm.end_date) {
    params.end_date = searchForm.end_date
  }
  if (searchForm.min_amount !== undefined && searchForm.min_amount !== '') {
    params.min_amount = searchForm.min_amount
  }
  if (searchForm.max_amount !== undefined && searchForm.max_amount !== '') {
    params.max_amount = searchForm.max_amount
  }
  return params
}

const loadOrders = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const params = {
      ...getSearchParams(),
      skip,
      limit: pageSize.value
    }
    const response = await api.get('/purchase-orders/', { params })
    orders.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadOrders()
}

const handleReset = () => {
  searchForm.supplier_id = undefined
  searchForm.status = ''
  searchForm.dateRange = []
  searchForm.start_date = ''
  searchForm.end_date = ''
  searchForm.min_amount = undefined
  searchForm.max_amount = undefined
  currentPage.value = 1
  loadOrders()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadOrders()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadOrders()
}

const loadSuppliers = async () => {
  try {
    const response = await api.get('/suppliers/', { params: { limit: 1000 } })
    suppliers.value = response.data.items
  } catch (error) {
    console.error('加载供应商列表失败', error)
  }
}

const loadProducts = async () => {
  try {
    const response = await api.get('/products/', { params: { limit: 1000 } })
    products.value = response.data.items
  } catch (error) {
    console.error('加载商品列表失败', error)
  }
}

const handleAdd = () => {
  editingId.value = null
  dialogTitle.value = '新增订单'
  Object.assign(form, {
    order_date: new Date(),
    supplier_id: null,
    source_sales_order_id: null,
    remark: '',
    items: []
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑订单'
  Object.assign(form, {
    order_date: new Date(row.order_date),
    supplier_id: row.supplier_id,
    source_sales_order_id: row.source_sales_order_id,
    remark: row.remark || '',
    items: row.items.map(item => ({
      product_id: item.product_id,
      quantity: item.quantity,
      unit_price: item.unit_price,
      line_total: item.line_total
    }))
  })
  dialogVisible.value = true
}

const handleView = (row) => {
  handleEdit(row)
}

const addItem = () => {
  form.items.push({
    product_id: null,
    quantity: 1,
    unit_price: 0,
    line_total: 0
  })
}

const removeItem = (index) => {
  form.items.splice(index, 1)
}

const handleProductChange = (index) => {
  const product = products.value.find(p => p.id === form.items[index].product_id)
  if (product) {
    form.items[index].unit_price = product.purchase_price || 0
    calculateItem(index)
  }
}

const calculateItem = (index) => {
  const item = form.items[index]
  item.line_total = item.quantity * item.unit_price
}

const calculateTotal = () => {
  return form.items.reduce((sum, item) => sum + (item.line_total || 0), 0)
}

const handleSubmit = async () => {
  if (!form.supplier_id) {
    ElMessage.warning('请选择供应商')
    return
  }
  if (form.items.length === 0) {
    ElMessage.warning('请添加至少一个商品')
    return
  }

  try {
    const payload = {
      order_date: form.order_date.toISOString(),
      supplier_id: form.supplier_id,
      source_sales_order_id: form.source_sales_order_id,
      remark: form.remark,
      items: form.items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price
      }))
    }

    if (editingId.value) {
      await api.put(`/purchase-orders/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/purchase-orders/', payload)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该订单吗？', '提示', { type: 'warning' })
    await api.delete(`/purchase-orders/${row.id}`)
    ElMessage.success('删除成功')
    loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 修改采购状态
const handlePurchaseStatusChange = async (order) => {
  try {
    await api.put(`/purchase-orders/${order.id}/purchase-status`, {
      purchase_status: order.purchase_status
    })
    ElMessage.success('状态更新成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '状态更新失败')
    // 恢复原状态
    await loadOrders()
  }
}

// 打开入库对话框
const handleReceive = async (row) => {
  currentOrder.value = row
  // 初始化入库数量
  receiveItems.value = row.items.map(item => ({
    ...item,
    receive_quantity: 0
  }))
  receiveDialogVisible.value = true
}

// 确认入库
const handleConfirmReceive = async () => {
  // 过滤出本次入库数量大于 0 的商品
  const itemsToReceive = receiveItems.value
    .filter(item => item.receive_quantity > 0)

  if (itemsToReceive.length === 0) {
    ElMessage.warning('请输入入库数量')
    return
  }

  // 检查采购状态
  if (currentOrder.value.purchase_status !== '已下单') {
    ElMessage.error(`采购订单状态为「${currentOrder.value.purchase_status}」，尚未下单给供应商，无法入库`)
    return
  }

  try {
    const payload = {
      items: itemsToReceive.map(item => ({
        order_item_id: item.id,
        received_quantity: item.receive_quantity
      }))
    }

    await api.post(`/purchase-orders/${currentOrder.value.id}/receive`, payload)
    ElMessage.success('入库成功')
    receiveDialogVisible.value = false
    loadOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '入库失败')
  }
}

onMounted(() => {
  loadOrders()
  loadSuppliers()
  loadProducts()
})
</script>

<style scoped>
.purchase-orders-container {
  width: 100%;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.search-box {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

.pagination-container {
  display: flex;
  justify-content: flex-end;
  padding: 15px 0 0 0;
  margin-top: 15px;
  border-top: 1px solid #ebeef5;
}

:deep(.el-table__body-wrapper) {
  overflow-x: auto !important;
}

:deep(.el-table__header-wrapper) {
  overflow-x: auto !important;
}

:deep(.el-table td) {
  padding: 8px 0;
}

:deep(.el-table__row) {
  height: auto;
}
</style>
