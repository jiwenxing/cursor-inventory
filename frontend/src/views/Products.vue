<template>
  <div>
    <div class="header">
      <h2>商品管理</h2>
      <el-button type="primary" @click="handleAdd">新增商品</el-button>
    </div>
    
    <el-table :data="products" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="商品名称" />
      <el-table-column prop="model" label="型号" />
      <el-table-column prop="brand" label="品牌" />
      <el-table-column prop="unit" label="单位" />
      <el-table-column prop="tax_rate" label="税率">
        <template #default="{ row }">
          {{ (row.tax_rate * 100).toFixed(0) }}%
        </template>
      </el-table-column>
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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

const rules = {
  name: [{ required: true, message: '请输入商品名称', trigger: 'blur' }],
  model: [{ required: true, message: '请输入型号', trigger: 'blur' }]
}

const loadProducts = async () => {
  loading.value = true
  try {
    const response = await api.get('/products/')
    products.value = response.data
  } catch (error) {
    ElMessage.error('加载商品列表失败')
  } finally {
    loading.value = false
  }
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
        loadProducts()
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
    loadProducts()
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
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
</style>
