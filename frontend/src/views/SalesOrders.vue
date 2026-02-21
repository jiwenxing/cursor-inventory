<template>
  <div>
    <div class="header">
      <h2>销售订单</h2>
      <el-button type="primary" @click="handleAdd">新增订单</el-button>
    </div>
    
    <el-table :data="orders" style="width: 100%" v-loading="loading">
      <el-table-column prop="id" label="订单号" width="100" />
      <el-table-column prop="order_date" label="订单日期" width="120">
        <template #default="{ row }">
          {{ formatDate(row.order_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" />
      <el-table-column prop="total_amount" label="订单金额" width="120">
        <template #default="{ row }">
          ¥{{ row.total_amount.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column prop="payment_status" label="付款状态" width="100" />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleView(row)">查看</el-button>
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

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

const loadOrders = async () => {
  loading.value = true
  try {
    const response = await api.get('/sales-orders/')
    orders.value = response.data
  } catch (error) {
    ElMessage.error('加载订单列表失败')
  } finally {
    loading.value = false
  }
}

const loadCustomers = async () => {
  try {
    const response = await api.get('/customers/')
    customers.value = response.data
  } catch (error) {
    console.error('加载客户列表失败', error)
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
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
