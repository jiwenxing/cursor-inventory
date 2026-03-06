<template>
  <div class="sales-orders-container">
    <div class="header">
      <h2>销售订单</h2>
      <el-button type="primary" @click="handleAdd">新增订单</el-button>
    </div>

    <!-- 搜索过滤区域 -->
    <div class="search-box">
      <el-row :gutter="15" style="margin-bottom: 15px;">
        <el-col :span="4">
          <el-select
            v-model="searchForm.customer_id"
            placeholder="选择客户"
            filterable
            clearable
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option
              v-for="c in customers"
              :key="c.id"
              :label="c.name"
              :value="c.id"
            />
          </el-select>
        </el-col>
        <el-col :span="4">
          <el-select
            v-model="searchForm.payment_status"
            placeholder="付款状态"
            clearable
            @change="handleSearch"
            style="width: 100%"
          >
            <el-option label="未付款" value="未付款" />
            <el-option label="部分付款" value="部分付款" />
            <el-option label="已付款" value="已付款" />
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
            @change="handleDateRangeChange"
            style="width: 100%"
          />
        </el-col>
        <el-col :span="2">
          <el-button-group>
            <el-button @click="setQuickDate('today')">今天</el-button>
            <el-button @click="setQuickDate('week')">近一周</el-button>
            <el-button @click="setQuickDate('month')">近一月</el-button>
          </el-button-group>
        </el-col>
        <el-col :span="2">
          <el-button-group>
            <el-button @click="setQuickDate('3months')">3个月</el-button>
            <el-button @click="setQuickDate('halfyear')">半年</el-button>
          </el-button-group>
        </el-col>
        <el-col :span="3">
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
              <el-table-column prop="unit_price_tax" label="单价(含税)" width="90">
                <template #default="{ row }">
                  ¥{{ row.unit_price_tax?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="discount_rate" label="折扣" width="70">
                <template #default="{ row }">
                  {{ (row.discount_rate * 100).toFixed(0) }}%
                </template>
              </el-table-column>
              <el-table-column prop="line_total" label="行金额" width="90">
                <template #default="{ row }">
                  ¥{{ row.line_total?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="shipped_quantity" label="已发货" width="70" />
              <el-table-column prop="unshipped_quantity" label="未发货" width="70" />
            </el-table>
          </div>
        </template>
      </el-table-column>
      <el-table-column prop="id" label="订单号" width="70" />
      <el-table-column prop="order_date" label="订单日期" width="130">
        <template #default="{ row }">
          {{ formatDate(row.order_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" show-overflow-tooltip />
      <el-table-column prop="salesperson_name" label="销售员" width="80" />
      <el-table-column prop="total_amount" label="订单金额" width="100">
        <template #default="{ row }">
          ¥{{ row.total_amount?.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column label="已开票" width="90">
        <template #default="{ row }">
          <span style="color: #909399;">¥{{ (row.invoiced_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="可开票" width="90">
        <template #default="{ row }">
          <span :style="{ color: (row.balance_amount || 0) > 0 ? '#67c23a' : '#909399' }">
            ¥{{ (row.balance_amount || 0).toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="payment_status" label="付款状态" width="90" />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleView(row)">查看</el-button>
          <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
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
            <el-form-item label="客户" prop="customer_id">
              <el-select v-model="form.customer_id" filterable style="width: 100%">
                <el-option
                  v-for="customer in customers"
                  :key="customer.id"
                  :label="customer.name"
                  :value="customer.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="合同金额" prop="contract_amount">
              <el-input-number v-model="form.contract_amount" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="付款状态" prop="payment_status">
              <el-select v-model="form.payment_status" style="width: 100%">
                <el-option label="未付款" value="未付款" />
                <el-option label="部分付款" value="部分付款" />
                <el-option label="已付款" value="已付款" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>订单明细</el-divider>
        <el-table :data="form.items" border>
          <el-table-column label="商品" width="200">
            <template #default="{ row, $index }">
              <el-select v-model="row.product_id" filterable @change="handleProductChange($index)">
                <el-option
                  v-for="product in products"
                  :key="product.id"
                  :label="`${product.name} (${product.model})`"
                  :value="product.id"
                />
              </el-select>
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="0.01" :precision="2" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="单价（含税）" width="120">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price_tax" :min="0" :precision="2" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="折扣率" width="100">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.discount_rate" :min="-1" :max="1" :step="0.01" :precision="2" @change="calculateItem($index)" />
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
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import dayjs from 'dayjs'

const orders = ref([])
const customers = ref([])
const products = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增订单')
const formRef = ref(null)
const editingId = ref(null)

// 分页相关
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

// 搜索表单
const searchForm = reactive({
  customer_id: undefined,
  payment_status: '',
  dateRange: [],
  start_date: '',
  end_date: '',
  min_amount: undefined,
  max_amount: undefined
})

const form = reactive({
  order_date: new Date(),
  customer_id: null,
  contract_amount: 0,
  payment_status: '未付款',
  items: []
})

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm')
}

// 快速选择日期
const setQuickDate = (type) => {
  const now = dayjs()
  let start, end

  switch (type) {
    case 'today':
      start = now.format('YYYY-MM-DD')
      end = now.format('YYYY-MM-DD')
      break
    case 'week':
      start = now.subtract(1, 'week').format('YYYY-MM-DD')
      end = now.format('YYYY-MM-DD')
      break
    case 'month':
      start = now.subtract(1, 'month').format('YYYY-MM-DD')
      end = now.format('YYYY-MM-DD')
      break
    case '3months':
      start = now.subtract(3, 'month').format('YYYY-MM-DD')
      end = now.format('YYYY-MM-DD')
      break
    case 'halfyear':
      start = now.subtract(6, 'month').format('YYYY-MM-DD')
      end = now.format('YYYY-MM-DD')
      break
  }

  searchForm.dateRange = [start, end]
  searchForm.start_date = start
  searchForm.end_date = end
  handleSearch()
}

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
  if (searchForm.customer_id !== undefined && searchForm.customer_id !== '') {
    params.customer_id = searchForm.customer_id
  }
  if (searchForm.payment_status) {
    params.payment_status = searchForm.payment_status
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
    const response = await api.get('/sales-orders/', { params })
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
  searchForm.customer_id = undefined
  searchForm.payment_status = ''
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

const loadCustomers = async () => {
  try {
    const response = await api.get('/customers/', { params: { limit: 1000 } })
    customers.value = response.data.items
  } catch (error) {
    console.error('加载客户列表失败', error)
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
    customer_id: null,
    contract_amount: 0,
    payment_status: '未付款',
    items: []
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑订单'
  Object.assign(form, {
    order_date: new Date(row.order_date),
    customer_id: row.customer_id,
    contract_amount: row.contract_amount,
    payment_status: row.payment_status,
    items: row.items.map(item => ({
      product_id: item.product_id,
      quantity: item.quantity,
      unit_price_tax: item.unit_price_tax,
      discount_rate: item.discount_rate,
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
    unit_price_tax: 0,
    discount_rate: 0,
    line_total: 0
  })
}

const removeItem = (index) => {
  form.items.splice(index, 1)
}

const handleProductChange = (index) => {
  const product = products.value.find(p => p.id === form.items[index].product_id)
  if (product) {
    form.items[index].unit_price_tax = 0
    calculateItem(index)
  }
}

const calculateItem = (index) => {
  const item = form.items[index]
  const finalPrice = item.unit_price_tax * (1 - item.discount_rate)
  item.line_total = item.quantity * finalPrice
}

const calculateTotal = () => {
  return form.items.reduce((sum, item) => sum + (item.line_total || 0), 0)
}

const handleSubmit = async () => {
  if (!form.customer_id) {
    ElMessage.warning('请选择客户')
    return
  }
  if (form.items.length === 0) {
    ElMessage.warning('请添加至少一个商品')
    return
  }

  try {
    const payload = {
      order_date: form.order_date.toISOString(),
      customer_id: form.customer_id,
      contract_amount: form.contract_amount,
      payment_status: form.payment_status,
      items: form.items.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price_tax: item.unit_price_tax,
        discount_rate: item.discount_rate
      }))
    }

    if (editingId.value) {
      await api.put(`/sales-orders/${editingId.value}`, payload)
      ElMessage.success('更新成功')
    } else {
      await api.post('/sales-orders/', payload)
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
    await api.delete(`/sales-orders/${row.id}`)
    ElMessage.success('删除成功')
    loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadOrders()
  loadCustomers()
  loadProducts()
})
</script>

<style scoped>
.sales-orders-container {
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