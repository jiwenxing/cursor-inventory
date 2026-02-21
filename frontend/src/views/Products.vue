<template>
  <div class="products-container">
    <div class="header">
      <h2>商品管理</h2>
      <el-button type="primary" @click="handleAdd">新增商品</el-button>
    </div>
    
    <div class="search-box">
      <el-row :gutter="15" style="margin-bottom: 15px;">
        <el-col :span="6">
          <el-input 
            v-model="searchForm.search" 
            placeholder="搜索商品名称、型号、品牌..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="5">
          <el-input 
            v-model="searchForm.name"
            placeholder="商品名称"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="5">
          <el-input 
            v-model="searchForm.model"
            placeholder="型号"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="5">
          <el-input 
            v-model="searchForm.brand"
            placeholder="品牌"
            clearable
            @input="handleSearch"
          />
        </el-col>
        <el-col :span="3">
          <el-button @click="handleReset" plain>重置</el-button>
        </el-col>
      </el-row>
    </div>
    
    <el-table :data="products" style="width: 100%" v-loading="loading" :default-sort="{ prop: 'id', order: 'ascending' }">
      <el-table-column prop="name" label="商品名称" show-overflow-tooltip />
      <el-table-column prop="model" label="型号" width="120" show-overflow-tooltip />
      <el-table-column prop="brand" label="品牌" width="120" show-overflow-tooltip />
      <el-table-column prop="unit" label="单位" width="80" />
      <el-table-column prop="tax_rate" label="税率" width="80">
        <template #default="{ row }">
          {{ (row.tax_rate * 100).toFixed(0) }}%
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" link type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="商品名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="型号" prop="model">
          <el-input v-model="form.model" :disabled="!!editingId" />
        </el-form-item>
        <el-form-item label="品牌" prop="brand">
          <el-input v-model="form.brand" />
        </el-form-item>
        <el-form-item label="单位" prop="unit">
          <el-input v-model="form.unit" />
        </el-form-item>
        <el-form-item label="税率" prop="tax_rate">
          <el-input-number v-model="form.tax_rate" :min="0" :max="1" :step="0.01" :precision="2" />
        </el-form-item>
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
import { Search } from '@element-plus/icons-vue'
import api from '../api'

const products = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增商品')
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  model: '',
  brand: '',
  unit: '件',
  tax_rate: 0.13
})

const searchForm = reactive({
  search: '',
  name: '',
  model: '',
  brand: ''
})

const rules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  model: [{ required: true, message: '请输入型号', trigger: 'blur' }]
}

const loadProducts = async (params = {}) => {
  loading.value = true
  try {
    const response = await api.get('/products/', { params })
    products.value = response.data
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  // 构建查询参数
  const params = {}
  if (searchForm.search) params.search = searchForm.search
  if (searchForm.name) params.name = searchForm.name
  if (searchForm.model) params.model = searchForm.model
  if (searchForm.brand) params.brand = searchForm.brand
  
  loadProducts(params)
}

const handleReset = () => {
  searchForm.search = ''
  searchForm.name = ''
  searchForm.model = ''
  searchForm.brand = ''
  loadProducts()
}

const handleAdd = () => {
  editingId.value = null
  dialogTitle.value = '新增商品'
  Object.assign(form, { name: '', model: '', brand: '', unit: '件', tax_rate: 0.13 })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑商品'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (editingId.value) {
          await api.put(`/products/${editingId.value}`, form)
          ElMessage.success('更新成功')
        } else {
          await api.post('/products/', form)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        handleSearch()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该商品吗？', '提示', { type: 'warning' })
    await api.delete(`/products/${row.id}`)
    ElMessage.success('删除成功')
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadProducts()
})
</script>

<style scoped>
.products-container {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.search-box {
  background-color: #f5f7fa;
  padding: 15px;
  border-radius: 4px;
  margin-bottom: 15px;
}

:deep(.el-table) {
  width: 100% !important;
  flex: 1;
}
</style>
