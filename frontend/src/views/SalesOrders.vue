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
            <h4 style="margin-bottom: 15px;">订单详情</h4>
            <div style="display: flex; gap: 30px; margin-bottom: 20px; font-size: 14px;">
              <div>合同编号：{{ row.contract_no || '-' }}</div>
              <div>合同日期：{{ row.contract_date ? formatDate(row.contract_date).split(' ')[0] : '-' }}</div>
              <div>合同金额：¥{{ (row.contract_amount || 0).toFixed(2) }}</div>
            </div>

            <h4 style="margin-bottom: 15px;">订单明细</h4>
            <el-table :data="row.items" style="width: 100%" :show-header="true" size="small">
              <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
              <el-table-column prop="product_model" label="型号" width="100" />
              <el-table-column prop="customer_product_code" label="客户商品编号" width="120" />
              <el-table-column prop="quantity" label="数量" width="70" />
              <el-table-column prop="unit_price_tax" label="含税单价" width="100">
                <template #default="{ row }">
                  ¥{{ row.unit_price_tax?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="discounted_price_tax" label="含税优惠价" width="100">
                <template #default="{ row }">
                  ¥{{ row.discounted_price_tax?.toFixed(2) }}
                </template>
              </el-table-column>
              <el-table-column prop="discount_rate" label="折扣率" width="70">
                <template #default="{ row }">
                  {{ (row.discount_rate * 100).toFixed(2) }}%
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
      <el-table-column prop="id" label="订单号" width="100" />
      <el-table-column prop="order_date" label="订单日期" width="160">
        <template #default="{ row }">
          {{ formatDate(row.order_date) }}
        </template>
      </el-table-column>
      <el-table-column prop="customer_name" label="客户" show-overflow-tooltip />
      <el-table-column prop="salesperson_name" label="销售员" width="100" />
      <el-table-column prop="total_amount" label="订单金额" width="110">
        <template #default="{ row }">
          ¥{{ row.total_amount?.toFixed(2) }}
        </template>
      </el-table-column>
      <el-table-column label="已开票" width="110">
        <template #default="{ row }">
          <span style="color: #909399;">¥{{ (row.invoiced_amount || 0).toFixed(2) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="可开票" width="110">
        <template #default="{ row }">
          <span :style="{ color: (row.balance_amount || 0) > 0 ? '#67c23a' : '#909399' }">
            ¥{{ (row.balance_amount || 0).toFixed(2) }}
          </span>
        </template>
      </el-table-column>
      <el-table-column prop="payment_status" label="付款状态" width="110" />
      <el-table-column label="已付/未付" width="160">
        <template #default="{ row }">
          <div style="display: flex; flex-direction: column; gap: 4px;">
            <span style="color: #67c23a;">已付：¥{{ (row.paid_amount || 0).toFixed(2) }}</span>
            <span :style="{ color: (row.unpaid_amount || 0) > 0 ? '#f56c6c' : '#909399' }">
              未付：¥{{ (row.unpaid_amount || 0).toFixed(2) }}
            </span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="280" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleView(row)">查看</el-button>
          <el-button size="small" link type="primary" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" link type="success" @click="handlePayment(row)">收款</el-button>
          <el-button size="small" link type="warning" @click="handleInvoice(row)" :disabled="(row.balance_amount || 0) <= 0">开票</el-button>
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
            <el-form-item label="合同编号" prop="contract_no">
              <el-input v-model="form.contract_no" placeholder="请输入合同编号" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="合同日期" prop="contract_date">
              <el-date-picker v-model="form.contract_date" type="date" style="width: 100%" value-format="YYYY-MM-DD" placeholder="请选择合同日期" />
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
          <el-table-column label="客户商品编号" min-width="100" align="center">
            <template #default="{ row, $index }">
              <el-input v-model="row.customer_product_code" placeholder="客户商品编号" size="small" style="width: 100%" />
            </template>
          </el-table-column>
          <el-table-column label="数量" width="100" align="center">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.quantity" :min="1" :step="1" size="small" style="width: 90%" controls-position="right" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="含税单价" width="110" align="center">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.unit_price_tax" :min="0" :precision="2" size="small" controls-position="right" @change="calculateItem($index)" />
            </template>
          </el-table-column>
          <el-table-column label="含税优惠价" width="110" align="center">
            <template #default="{ row, $index }">
              <el-input-number v-model="row.discounted_price_tax" :min="0" :precision="2" size="small" controls-position="right" @change="handleDiscountedPriceChange($index)" />
            </template>
          </el-table-column>
          <el-table-column label="折扣率" width="90" align="center">
            <template #default="{ row }">
              {{ calculateDiscountRate(row) }}%
            </template>
          </el-table-column>
          <el-table-column label="行金额" width="110">
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

    <!-- 收款记录对话框 -->
    <el-dialog v-model="paymentDialogVisible" title="收款记录" width="900px">
      <div v-if="currentOrder" style="margin-bottom: 20px;">
        <el-descriptions title="订单信息" :column="3" border>
          <el-descriptions-item label="订单号">{{ currentOrder.id }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ currentOrder.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="订单日期">{{ formatDate(currentOrder.order_date) }}</el-descriptions-item>
          <el-descriptions-item label="订单金额">¥{{ (currentOrder.total_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="已付金额">¥{{ (currentOrder.paid_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="未付金额">¥{{ (currentOrder.unpaid_amount || 0).toFixed(2) }}</el-descriptions-item>
        </el-descriptions>
      </div>

      <!-- 新增收款 -->
      <el-form :model="paymentForm" ref="paymentFormRef" label-width="100px" style="margin-bottom: 20px;">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="收款金额" prop="amount">
              <el-input-number v-model="paymentForm.amount" :min="0" :precision="2" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="收款日期" prop="payment_date">
              <el-date-picker v-model="paymentForm.payment_date" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="收款方式" prop="payment_method">
              <el-select v-model="paymentForm.payment_method" style="width: 100%">
                <el-option label="银行转账" value="银行转账" />
                <el-option label="现金" value="现金" />
                <el-option label="承兑汇票" value="承兑汇票" />
                <el-option label="支票" value="支票" />
                <el-option label="其他" value="其他" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <el-row :gutter="20">
          <el-col :span="20">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="paymentForm.remark" placeholder="请输入备注" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="4">
            <el-button type="primary" @click="handleAddPayment" style="width: 100%">添加收款</el-button>
          </el-col>
        </el-row>
      </el-form>

      <!-- 收款记录列表 -->
      <el-table :data="paymentRecords" style="width: 100%" max-height="400">
        <el-table-column prop="payment_date" label="收款日期" width="160">
          <template #default="{ row }">
            {{ formatDate(row.payment_date) }}
          </template>
        </el-table-column>
        <el-table-column prop="payment_method" label="收款方式" width="100" />
        <el-table-column prop="amount" label="收款金额" width="120">
          <template #default="{ row }">
            <span style="color: #67c23a;">¥{{ row.amount?.toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" show-overflow-tooltip />
        <el-table-column prop="creator_name" label="创建人" width="100" />
        <el-table-column label="操作" width="80">
          <template #default="{ row }">
            <el-button size="small" type="danger" link @click="handleDeletePayment(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>

    <!-- 开票对话框 -->
    <el-dialog v-model="invoiceDialogVisible" title="开票" width="1000px" @close="invoiceDialogVisible = false">
      <div v-if="invoiceOrderInfo" style="margin-bottom: 20px;">
        <el-descriptions title="订单信息" :column="3" border>
          <el-descriptions-item label="订单号">{{ invoiceOrderInfo.order_id }}</el-descriptions-item>
          <el-descriptions-item label="客户">{{ invoiceOrderInfo.customer_name }}</el-descriptions-item>
          <el-descriptions-item label="订单日期">{{ formatDate(invoiceOrderInfo.order_date) }}</el-descriptions-item>
          <el-descriptions-item label="订单金额">¥{{ (invoiceOrderInfo.total_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="已开票">¥{{ (invoiceOrderInfo.invoiced_amount || 0).toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="可开票余额">
            <span style="color: #67c23a; font-weight: bold;">¥{{ (invoiceOrderInfo.balance_amount || 0).toFixed(2) }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>

      <el-divider>选择开票商品</el-divider>
      <el-table :data="invoiceOrderInfo?.items || []" style="width: 100%" max-height="400" @selection-change="handleInvoiceSelectionChange">
        <el-table-column type="selection" width="50" :selectable="(row) => row.available_quantity > 0" />
        <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
        <el-table-column prop="product_model" label="型号" width="100" />
        <el-table-column prop="quantity" label="订单数量" width="90" align="right" />
        <el-table-column prop="invoiced_quantity" label="已开票数量" width="100" align="right">
          <template #default="{ row }">
            <span style="color: #909399;">{{ row.invoiced_quantity || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="available_quantity" label="可开票数量" width="100" align="right">
          <template #default="{ row }">
            <span style="color: #67c23a;">{{ row.available_quantity || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="discounted_price_tax" label="含税优惠价" width="100" align="right">
          <template #default="{ row }">
            ¥{{ (row.discounted_price_tax || 0).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column prop="available_amount" label="可开票金额" width="110" align="right">
          <template #default="{ row }">
            <span style="color: #67c23a;">¥{{ (row.available_amount || 0).toFixed(2) }}</span>
          </template>
        </el-table-column>
      </el-table>

      <!-- 开票表单 -->
      <el-form :model="invoiceForm" ref="invoiceFormRef" label-width="100px" style="margin-top: 20px;">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="发票号" prop="invoice_no">
              <el-input v-model="invoiceForm.invoice_no" placeholder="自动生成" disabled />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="开票日期" prop="invoice_date">
              <el-date-picker v-model="invoiceForm.invoice_date" type="datetime" style="width: 100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="备注" prop="remark">
              <el-input v-model="invoiceForm.remark" placeholder="可选" />
            </el-form-item>
          </el-col>
        </el-row>

        <el-divider>已选商品明细</el-divider>
        <el-table :data="selectedInvoiceItems" style="width: 100%" max-height="300">
          <el-table-column prop="product_name" label="商品" show-overflow-tooltip />
          <el-table-column prop="product_model" label="型号" width="100" />
          <el-table-column label="可开票数量" width="100" align="right">
            <template #default="{ row }">
              {{ row.available_quantity }}
            </template>
          </el-table-column>
          <el-table-column label="本次开票数量" width="140" align="center">
            <template #default="{ row, $index }">
              <el-input-number
                v-model="row.invoice_quantity"
                :min="0.01"
                :max="row.available_quantity"
                :step="1"
                size="small"
                controls-position="right"
                @change="handleInvoiceQuantityChange($index)"
              />
            </template>
          </el-table-column>
          <el-table-column label="含税优惠价" width="100" align="right">
            <template #default="{ row }">
              ¥{{ (row.discounted_price_tax || 0).toFixed(2) }}
            </template>
          </el-table-column>
          <el-table-column label="开票金额" width="110" align="right">
            <template #default="{ row }">
              <span style="color: #e6a23c; font-weight: bold;">¥{{ (row.invoice_amount || 0).toFixed(2) }}</span>
            </template>
          </el-table-column>
        </el-table>

        <div style="margin-top: 20px; text-align: right;">
          <el-button @click="selectAllInvoiceItems">全选</el-button>
          <el-button @click="clearInvoiceItems">清空</el-button>
          <span style="margin-left: 20px; font-size: 16px;">
            <strong>开票总金额：</strong>
            <span style="color: #e6a23c; font-size: 18px;">¥{{ calculateInvoiceTotal().toFixed(2) }}</span>
          </span>
        </div>
      </el-form>

      <template #footer>
        <el-button @click="invoiceDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitInvoice" :disabled="selectedInvoiceItems.length === 0 || calculateInvoiceTotal() <= 0">确认开票</el-button>
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
const paymentDialogVisible = ref(false)
const dialogTitle = ref('新增订单')
const formRef = ref(null)
const paymentFormRef = ref(null)
const editingId = ref(null)
const currentOrder = ref(null)
const paymentRecords = ref([])

// 开票相关
const invoiceDialogVisible = ref(false)
const invoiceFormRef = ref(null)
const invoiceOrderInfo = ref(null)
const selectedInvoiceItems = ref([])
const invoiceForm = reactive({
  invoice_no: '',
  invoice_date: new Date(),
  remark: ''
})

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
  contract_no: '',
  contract_date: null,
  contract_amount: 0,
  payment_status: '未付款',
  items: []
})

const paymentForm = reactive({
  amount: 0,
  payment_date: new Date(),
  payment_method: '银行转账',
  remark: ''
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
    contract_no: '',
    contract_date: null,
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
    contract_no: row.contract_no || '',
    contract_date: row.contract_date ? new Date(row.contract_date) : null,
    contract_amount: row.contract_amount,
    payment_status: row.payment_status,
    items: row.items.map(item => ({
      product_id: item.product_id,
      customer_product_code: item.customer_product_code || '',
      quantity: item.quantity,
      unit_price_tax: item.unit_price_tax,
      discounted_price_tax: item.discounted_price_tax || item.unit_price_tax,
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
    customer_product_code: '',
    quantity: 1,
    unit_price_tax: 0,
    discounted_price_tax: 0,
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
    form.items[index].unit_price_tax = product.retail_price || 0
    form.items[index].discounted_price_tax = product.retail_price || 0
    calculateItem(index)
  }
}

const calculateItem = (index) => {
  const item = form.items[index]
  item.line_total = item.quantity * item.discounted_price_tax
}

const handleDiscountedPriceChange = (index) => {
  calculateItem(index)
}

const calculateDiscountRate = (item) => {
  if (!item.unit_price_tax || item.unit_price_tax === 0) {
    return '0'
  }
  const rate = (1 - item.discounted_price_tax / item.unit_price_tax) * 100
  return rate.toFixed(2)
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
      contract_no: form.contract_no || null,
      contract_date: form.contract_date ? new Date(form.contract_date).toISOString() : null,
      contract_amount: form.contract_amount,
      payment_status: form.payment_status,
      items: form.items.map(item => ({
        product_id: item.product_id,
        customer_product_code: item.customer_product_code,
        quantity: item.quantity,
        unit_price_tax: item.unit_price_tax,
        discounted_price_tax: item.discounted_price_tax,
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

// 收款记录相关方法
const handlePayment = async (row) => {
  currentOrder.value = row
  paymentForm.amount = row.unpaid_amount || 0
  paymentForm.payment_date = new Date()
  paymentForm.payment_method = '银行转账'
  paymentForm.remark = ''
  await loadPaymentRecords(row.id)
  paymentDialogVisible.value = true
}

const loadPaymentRecords = async (orderId) => {
  try {
    const response = await api.get(`/payment-records/order/${orderId}`)
    paymentRecords.value = response.data
  } catch (error) {
    console.error('加载收款记录失败', error)
  }
}

const handleAddPayment = async () => {
  if (!currentOrder.value) return

  if (paymentForm.amount <= 0) {
    ElMessage.warning('收款金额必须大于 0')
    return
  }

  if (paymentForm.amount > (currentOrder.value.unpaid_amount || 0)) {
    ElMessage.error('收款金额不能超过未付金额')
    return
  }

  try {
    const payload = {
      order_id: currentOrder.value.id,
      amount: paymentForm.amount,
      payment_date: paymentForm.payment_date.toISOString(),
      payment_method: paymentForm.payment_method,
      remark: paymentForm.remark
    }

    await api.post('/payment-records/', payload)
    ElMessage.success('添加收款成功')

    // 刷新收款记录
    await loadPaymentRecords(currentOrder.value.id)

    // 重新获取订单详情以更新对话框中的订单信息
    const orderResponse = await api.get(`/sales-orders/${currentOrder.value.id}`)
    const updatedOrder = orderResponse.data
    currentOrder.value.paid_amount = updatedOrder.paid_amount || 0
    currentOrder.value.unpaid_amount = updatedOrder.unpaid_amount || 0

    // 刷新订单列表
    await loadOrders()

    // 重置表单
    paymentForm.amount = 0
    paymentForm.remark = ''
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '添加收款失败')
  }
}

const handleDeletePayment = async (record) => {
  try {
    await ElMessageBox.confirm('确定要删除该收款记录吗？', '提示', { type: 'warning' })
    await api.delete(`/payment-records/${record.id}`)
    ElMessage.success('删除成功')
    await loadPaymentRecords(currentOrder.value.id)
    await loadOrders()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

// 开票相关方法
const handleInvoice = async (row) => {
  try {
    // 获取订单商品明细（包含已开票信息）
    const response = await api.get(`/invoices/orders/${row.id}/items-for-invoice`)
    invoiceOrderInfo.value = response.data

    // 确保有 customer_id（兼容旧版后端）
    if (!invoiceOrderInfo.value.customer_id) {
      invoiceOrderInfo.value.customer_id = row.customer_id
    }

    // 重置表单
    invoiceForm.remark = ''
    invoiceForm.invoice_date = new Date()

    // 获取下一个发票号
    const invoiceNoResponse = await api.get('/invoices/next-no')
    invoiceForm.invoice_no = invoiceNoResponse.data.invoice_no

    // 清空已选商品
    selectedInvoiceItems.value = []

    invoiceDialogVisible.value = true
  } catch (error) {
    ElMessage.error('加载订单开票信息失败')
    console.error(error)
  }
}

const handleInvoiceSelectionChange = (selection) => {
  // 转换选中的行为包含开票数量的对象
  selectedInvoiceItems.value = selection.map(item => ({
    order_item_id: item.id,
    product_name: item.product_name,
    product_model: item.product_model,
    quantity: item.quantity,
    available_quantity: item.available_quantity,
    invoiced_quantity: item.invoiced_quantity,
    discounted_price_tax: item.discounted_price_tax,
    invoice_quantity: item.available_quantity, // 默认填入可开票数量
    invoice_amount: item.available_amount // 默认填入可开票金额
  }))
}

const selectAllInvoiceItems = () => {
  // 选择所有可开票的商品
  selectedInvoiceItems.value = (invoiceOrderInfo.value?.items || [])
    .filter(item => item.available_quantity > 0)
    .map(item => ({
      order_item_id: item.id,
      product_name: item.product_name,
      product_model: item.product_model,
      quantity: item.quantity,
      available_quantity: item.available_quantity,
      invoiced_quantity: item.invoiced_quantity,
      discounted_price_tax: item.discounted_price_tax,
      invoice_quantity: item.available_quantity,
      invoice_amount: item.available_amount
    }))
}

const clearInvoiceItems = () => {
  selectedInvoiceItems.value = []
}

const handleInvoiceQuantityChange = (index) => {
  const item = selectedInvoiceItems.value[index]
  // 根据开票数量重新计算开票金额
  item.invoice_amount = item.invoice_quantity * item.discounted_price_tax
}

const calculateInvoiceTotal = () => {
  return selectedInvoiceItems.value.reduce((sum, item) => sum + (item.invoice_amount || 0), 0)
}

const handleSubmitInvoice = async () => {
  if (!invoiceForm.invoice_no) {
    ElMessage.warning('请填写发票号')
    return
  }

  if (selectedInvoiceItems.value.length === 0) {
    ElMessage.warning('请选择要开票的商品')
    return
  }

  const totalAmount = calculateInvoiceTotal()
  if (totalAmount <= 0) {
    ElMessage.warning('开票金额必须大于 0')
    return
  }

  if (totalAmount > (invoiceOrderInfo.value.balance_amount || 0)) {
    ElMessage.error('开票金额不能超过可开票余额')
    return
  }

  try {
    const items = selectedInvoiceItems.value.map(item => ({
      order_item_id: item.order_item_id,
      quantity: item.invoice_quantity,
      amount: item.invoice_amount,
      tax_amount: 0 // 税额暂时设为0，后续可扩展
    }))

    const payload = {
      invoice_no: invoiceForm.invoice_no,
      invoice_date: invoiceForm.invoice_date.toISOString(),
      customer_id: invoiceOrderInfo.value.customer_id,
      remark: invoiceForm.remark,
      items
    }

    await api.post('/invoices/from-order', payload)
    ElMessage.success('开票成功')

    invoiceDialogVisible.value = false

    // 刷新订单列表
    await loadOrders()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '开票失败')
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
