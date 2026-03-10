<template>
  <div class="invoices-container">
    <div class="header">
      <h2>发票管理</h2>
      <el-button type="primary" @click="handleAdd">新增开票</el-button>
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
          <el-input
            v-model="searchForm.invoice_no"
            placeholder="发票号"
            clearable
            @input="handleSearch"
          />
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
        <el-col :span="3">
          <el-button @click="handleReset" plain>重置</el-button>
        </el-col>
      </el-row>
    </div>

    <el-table :data="invoices" style="width: 100%" v-loading="loading" row-key="id">
      <el-table-column prop="invoice_no" label="发票号" width="160" />
      <el-table-column prop="invoice_date" label="开票日期" width="160">
        <template #default="{ row }">
          {{ formatDate(row.invoice_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" show-overflow-tooltip />
      <el-table-column label="关联订单号" width="120">
        <template #default="{ row }">
          <div v-if="row.items && row.items.length > 0">
            <el-tag v-for="item in row.items" :key="item.id" size="small" class="order-tag">
              {{ item.order_no }}
            </el-tag>
          </div>
          <span v-else>-</span>
        </template>
      </el-table-column>
      <el-table-column prop="total_amount" label="发票金额" width="110">
        <template #default="{ row }">
          ¥{{ row.total_amount.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="tax_amount" label="税额" width="100">
        <template #default="{ row }">
          ¥{{ row.tax_amount.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="status" label="状态" width="80">
        <template #default="{ row }">
          <el-tag :type="row.status === '已开票' ? 'success' : 'danger'" size="small">
            {{ row.status }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="creator_name" label="开票人" width="80" />
      <el-table-column prop="remark" label="备注" show-overflow-tooltip />
      <el-table-column label="操作" width="150" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleView(row)">查看</el-button>
          <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" link type="danger" @click="handleDelete(row)" :disabled="row.status === '已作废'">作废</el-button>
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

    <!-- 开票对话框 -->
    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="900px" @close="resetForm">
      <el-form :model="form" ref="formRef" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="发票号" prop="invoice_no">
              <el-input v-model="form.invoice_no" :disabled="!!editingId" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="开票日期" prop="invoice_date">
              <el-date-picker v-model="form.invoice_date" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="客户" prop="customer_id">
              <el-select
                v-model="form.customer_id"
                filterable
                style="width: 100%"
                @change="handleCustomerChange"
                :disabled="!!editingId"
              >
                <el-option
                  v-for="c in customers"
                  :key="c.id"
                  :label="c.name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="form.remark" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 可开票订单列表（新增时显示） -->
        <div v-if="!editingId && form.customer_id" style="margin-top: 20px;">
          <el-divider>选择要开票的订单</el-divider>
          <el-table :data="availableOrders" border size="small" max-height="250" style="width: 100%">
            <el-table-column width="50" align="center">
              <template #default="{ row, $index }">
                <el-checkbox
                  v-model="row.selected"
                  @change="handleOrderSelect($index)"
                />
              </template>
            </el-table-column>
            <el-table-column prop="order_no" label="订单号" width="100" align="center" />
            <el-table-column prop="order_date" label="订单日期" width="130" align="center">
              <template #default="{ row }">
                {{ formatDate(row.order_date) }}
              </template>
            </el-table-column>
            <el-table-column prop="total_amount" label="订单金额" width="110" align="right">
              <template #default="{ row }">
                ¥{{ row.total_amount.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="invoiced_amount" label="已开票" width="100" align="right">
              <template #default="{ row }">
                ¥{{ row.invoiced_amount.toFixed(2) }}
              </template>
            </el-table-column>
            <el-table-column prop="balance_amount" label="可开票" width="100" align="right">
              <template #default="{ row }">
                <span style="color: #67c23a; font-weight: bold;">¥{{ row.balance_amount.toFixed(2) }}</span>
              </template>
            </el-table-column>
            <el-table-column label="本次开票" min-width="140" align="center">
              <template #default="{ row }">
                <el-input-number
                  v-model="row.invoice_amount"
                  :min="0"
                  :max="row.balance_amount"
                  :precision="2"
                  size="small"
                  :disabled="!row.selected"
                  @change="calculateTotal"
                />
              </template>
            </el-table-column>
          </el-table>
          <div style="margin-top: 10px; text-align: right;">
            <span style="margin-right: 20px;">已选订单: {{ selectedOrderCount }} 张</span>
            <span>合计: <strong style="color: #f56c6c; font-size: 18px;">¥{{ calculateFormTotal().toFixed(2) }}</strong></span>
          </div>
        </div>

        <!-- 发票明细（编辑时显示） -->
        <div v-if="editingId" style="margin-top: 20px;">
          <el-divider>发票明细</el-divider>
          <el-table :data="form.items" border>
            <el-table-column prop="order_no" label="订单号" width="100" />
            <el-table-column label="开票金额" width="150">
              <template #default="{ row, $index }">
                <el-input-number
                  v-model="row.amount"
                  :min="0"
                  :precision="2"
                  @change="calculateFormTotal"
                />
              </template>
            </el-table-column>
            <el-table-column label="税额" width="150">
              <template #default="{ row, $index }">
                <el-input-number
                  v-model="row.tax_amount"
                  :min="0"
                  :precision="2"
                  @change="calculateFormTotal"
                />
              </template>
            </el-table-column>
            <el-table-column label="操作" width="80">
              <template #default="{ $index }">
                <el-button size="small" type="danger" @click="removeItem($index)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-button style="margin-top: 10px" @click="addItem">添加订单</el-button>

          <div style="margin-top: 20px; text-align: right">
            <strong>发票总额：¥{{ form.total_amount.toFixed(2) }}</strong>
          </div>
        </div>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">确定</el-button>
      </template>
    </el-dialog>

    <!-- 查看发票对话框 -->
    <el-dialog v-model="viewDialogVisible" title="发票详情" width="900px">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="发票号" :span="1">{{ viewData.invoice_no }}</el-descriptions-item>
        <el-descriptions-item label="状态" :span="1">
          <el-tag :type="viewData.status === '已开票' ? 'success' : 'danger'">
            {{ viewData.status }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="开票日期" :span="1">{{ formatDate(viewData.invoice_date) }}</el-descriptions-item>
        <el-descriptions-item label="客户" :span="1">{{ viewData.customer_name }}</el-descriptions-item>
        <el-descriptions-item label="发票金额" :span="1">¥{{ viewData.total_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="税额" :span="1">¥{{ viewData.tax_amount?.toFixed(2) }}</el-descriptions-item>
        <el-descriptions-item label="开票人" :span="1">{{ viewData.creator_name }}</el-descriptions-item>
        <el-descriptions-item label="备注" :span="1">{{ viewData.remark || '-' }}</el-descriptions-item>
      </el-descriptions>

      <el-divider>关联订单明细</el-divider>
      <div v-for="(item, index) in viewData.items" :key="item.id" class="order-detail-section">
        <div class="order-header">
          <span class="order-title">订单 #{{ item.order_no }}</span>
          <span class="order-info">订单日期: {{ item.order_date ? formatDate(item.order_date).split(' ')[0] : '-' }}</span>
          <span class="order-info">订单金额: ¥{{ item.order_total_amount?.toFixed(2) }}</span>
          <span class="order-info">本次开票: ¥{{ item.amount?.toFixed(2) }}</span>
        </div>

        <!-- 商品明细表格 -->
        <el-table v-if="item.product_items && item.product_items.length > 0" :data="item.product_items" border size="small" class="product-table">
          <el-table-column prop="product_name" label="商品名称" min-width="150" />
          <el-table-column prop="product_model" label="型号" width="120" />
          <el-table-column prop="quantity" label="开票数量" width="100" align="right" />
          <el-table-column prop="unit_price" label="单价" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.unit_price?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="amount" label="金额" width="120" align="right">
            <template #default="{ row }">
              ¥{{ row.amount?.toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column prop="tax_amount" label="税额" width="100" align="right">
            <template #default="{ row }">
              ¥{{ row.tax_amount?.toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>
        <div v-else class="no-product-data">无商品明细</div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import api from '../api'
import dayjs from 'dayjs'

const invoices = ref([])
const customers = ref([])
const availableOrders = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const viewDialogVisible = ref(false)
const dialogTitle = ref('新增开票')
const formRef = ref(null)
const editingId = ref(null)
const viewData = ref({})

const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

const searchForm = reactive({
  customer_id: undefined,
  invoice_no: '',
  dateRange: [],
  start_date: '',
  end_date: '',
  status: ''
})

const form = reactive({
  invoice_no: '',
  invoice_date: new Date(),
  customer_id: null,
  total_amount: 0,
  tax_amount: 0,
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

const getSearchParams = () => {
  const params = {}
  if (searchForm.customer_id !== undefined && searchForm.customer_id !== '') {
    params.customer_id = searchForm.customer_id
  }
  if (searchForm.invoice_no) {
    params.invoice_no = searchForm.invoice_no
  }
  if (searchForm.start_date) {
    params.start_date = searchForm.start_date
  }
  if (searchForm.end_date) {
    params.end_date = searchForm.end_date
  }
  if (searchForm.status) {
    params.status = searchForm.status
  }
  return params
}

const loadInvoices = async () => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const params = {
      ...getSearchParams(),
      skip,
      limit: pageSize.value
    }
    const response = await api.get('/invoices/', { params })
    invoices.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载发票列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadInvoices()
}

const handleReset = () => {
  searchForm.customer_id = undefined
  searchForm.invoice_no = ''
  searchForm.dateRange = []
  searchForm.start_date = ''
  searchForm.end_date = ''
  searchForm.status = ''
  currentPage.value = 1
  loadInvoices()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadInvoices()
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadInvoices()
}

const loadCustomers = async () => {
  try {
    const response = await api.get('/customers/', { params: { limit: 1000 } })
    customers.value = response.data.items
  } catch (error) {
    console.error('加载客户列表失败', error)
  }
}

const loadAvailableOrders = async (customerId) => {
  if (!customerId) {
    availableOrders.value = []
    return
  }
  try {
    const response = await api.get(`/invoices/orders/available`, { params: { customer_id: customerId } })
    availableOrders.value = response.data.map(o => ({
      ...o,
      selected: false,
      invoice_amount: 0
    }))
  } catch (error) {
    console.error('加载可开票订单失败', error)
  }
}

const handleCustomerChange = (customerId) => {
  if (!editingId.value) {
    loadAvailableOrders(customerId)
  }
  calculateFormTotal()
}

const selectedOrderCount = computed(() => {
  return availableOrders.value.filter(o => o.selected).length
})

const handleOrderSelect = (index) => {
  const order = availableOrders.value[index]
  if (order.selected) {
    order.invoice_amount = order.balance_amount
  } else {
    order.invoice_amount = 0
  }
  calculateFormTotal()
}

const calculateFormTotal = () => {
  let total = 0
  let tax = 0

  if (editingId.value) {
    form.items.forEach(item => {
      total += item.amount || 0
      tax += item.tax_amount || 0
    })
  } else {
    availableOrders.value.forEach(order => {
      if (order.selected) {
        total += order.invoice_amount || 0
        // 简化：税额按 13% 计算
        tax += (order.invoice_amount || 0) * 0.13
      }
    })
  }

  form.total_amount = total
  form.tax_amount = tax
  return total
}

const handleAdd = async () => {
  editingId.value = null
  dialogTitle.value = '新增开票'

  // 自动获取下一个发票号
  try {
    const response = await api.get('/invoices/next-no')
    form.invoice_no = response.data.invoice_no
  } catch (error) {
    form.invoice_no = ''
  }

  form.invoice_date = new Date()
  form.customer_id = null
  form.total_amount = 0
  form.tax_amount = 0
  form.remark = ''
  form.items = []
  availableOrders.value = []
  dialogVisible.value = true
}

const handleView = async (row) => {
  try {
    const response = await api.get(`/invoices/${row.id}`)
    viewData.value = response.data
    viewDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载发票详情失败')
  }
}

const handleEdit = async (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑发票'

  try {
    const response = await api.get(`/invoices/${row.id}`)
    const data = response.data
    form.invoice_no = data.invoice_no
    form.invoice_date = new Date(data.invoice_date)
    form.customer_id = data.customer_id
    form.total_amount = data.total_amount
    form.tax_amount = data.tax_amount
    form.remark = data.remark || ''
    form.items = data.items.map(item => ({
      order_id: item.order_id,
      order_no: item.order_no,
      amount: item.amount,
      tax_amount: item.tax_amount
    }))
    dialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载发票详情失败')
  }
}

const resetForm = () => {
  availableOrders.value = []
  editingId.value = null
}

const addItem = () => {
  form.items.push({
    order_id: null,
    order_no: null,
    amount: 0,
    tax_amount: 0
  })
}

const removeItem = (index) => {
  form.items.splice(index, 1)
  calculateFormTotal()
}

const handleSubmit = async () => {
  if (!form.invoice_no) {
    ElMessage.warning('请输入发票号')
    return
  }
  if (!form.customer_id) {
    ElMessage.warning('请选择客户')
    return
  }

  // 构建提交数据
  let submitData = {}
  if (editingId.value) {
    // 编辑模式
    if (form.items.length === 0) {
      ElMessage.warning('请添加至少一个订单')
      return
    }
    submitData = {
      invoice_no: form.invoice_no,
      invoice_date: form.invoice_date.toISOString(),
      customer_id: form.customer_id,
      total_amount: form.total_amount,
      tax_amount: form.tax_amount,
      remark: form.remark,
      items: form.items
    }
  } else {
    // 新增模式
    const selectedOrders = availableOrders.value.filter(o => o.selected && o.invoice_amount > 0)
    if (selectedOrders.length === 0) {
      ElMessage.warning('请选择要开票的订单')
      return
    }
    submitData = {
      invoice_no: form.invoice_no,
      invoice_date: form.invoice_date.toISOString(),
      customer_id: form.customer_id,
      total_amount: form.total_amount,
      tax_amount: form.tax_amount,
      remark: form.remark,
      items: selectedOrders.map(o => ({
        order_id: o.order_id,
        amount: o.invoice_amount,
        tax_amount: o.invoice_amount * 0.13
      }))
    }
  }

  try {
    if (editingId.value) {
      await api.put(`/invoices/${editingId.value}`, submitData)
      ElMessage.success('更新成功')
    } else {
      await api.post('/invoices/', submitData)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadInvoices()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要作废该发票吗？', '提示', { type: 'warning' })
    await api.delete(`/invoices/${row.id}`)
    ElMessage.success('发票已作废')
    loadInvoices()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '操作失败')
    }
  }
}

onMounted(() => {
  loadInvoices()
  loadCustomers()
})
</script>

<style scoped>
.invoices-container {
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

.order-tag {
  margin-right: 5px;
  margin-bottom: 2px;
}

.order-detail-section {
  margin-bottom: 20px;
  border: 1px solid #ebeef5;
  border-radius: 4px;
  padding: 15px;
  background-color: #fafafa;
}

.order-header {
  margin-bottom: 10px;
  padding-bottom: 10px;
  border-bottom: 1px solid #ebeef5;
}

.order-title {
  font-weight: bold;
  font-size: 14px;
  color: #303133;
  margin-right: 20px;
}

.order-info {
  font-size: 13px;
  color: #606266;
  margin-right: 15px;
}

.product-table {
  margin-top: 10px;
}

.no-product-data {
  color: #909399;
  font-size: 12px;
  text-align: center;
  padding: 10px;
}
</style>
