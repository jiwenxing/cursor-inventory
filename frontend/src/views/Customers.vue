<template>
  <div>
    <div class="header">
      <h2>客户管理</h2>
      <el-button type="primary" @click="handleAdd">新增客户</el-button>
    </div>
    
    <el-table :data="customers" style="width: 100%" v-loading="loading">
      <el-table-column prop="name" label="客户名称" />
      <el-table-column prop="code" label="客户编码" />
      <el-table-column prop="contact" label="联系人" />
      <el-table-column prop="phone" label="电话" />
      <el-table-column prop="address" label="地址" show-overflow-tooltip />
      <el-table-column label="操作" width="180">
        <template #default="{ row }">
          <el-button size="small" @click="handleEdit(row)">编辑</el-button>
          <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="客户名称" prop="name">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="客户编码" prop="code">
          <el-input v-model="form.code" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact">
          <el-input v-model="form.contact" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" type="textarea" />
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

const customers = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增客户')
const formRef = ref(null)
const editingId = ref(null)

const form = reactive({
  name: '',
  code: '',
  contact: '',
  phone: '',
  address: ''
})

const rules = {
  name: [{ required: true, message: '请输入客户名称', trigger: 'blur' }]
}

const loadCustomers = async () => {
  loading.value = true
  try {
    const response = await api.get('/customers/')
    customers.value = response.data
  } catch (error) {
    ElMessage.error('加载客户列表失败')
  } finally {
    loading.value = false
  }
}

const handleAdd = () => {
  editingId.value = null
  dialogTitle.value = '新增客户'
  Object.assign(form, { name: '', code: '', contact: '', phone: '', address: '' })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑客户'
  Object.assign(form, row)
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (editingId.value) {
          await api.put(`/customers/${editingId.value}`, form)
          ElMessage.success('更新成功')
        } else {
          await api.post('/customers/', form)
          ElMessage.success('创建成功')
        }
        dialogVisible.value = false
        loadCustomers()
      } catch (error) {
        ElMessage.error(error.response?.data?.detail || '操作失败')
      }
    }
  })
}

const handleDelete = async (row) => {
  try {
    await ElMessageBox.confirm('确定要删除该客户吗？', '提示', { type: 'warning' })
    await api.delete(`/customers/${row.id}`)
    ElMessage.success('删除成功')
    loadCustomers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadCustomers()
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
