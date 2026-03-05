<template>
  <div class="suppliers-container">
    <div class="header">
      <h2>供应商管理</h2>
      <el-button type="primary" @click="handleAdd">新增供应商</el-button>
    </div>

    <div class="search-box">
      <el-row :gutter="15">
        <el-col :span="4">
          <el-input
            v-model="searchForm.search"
            placeholder="搜索名称、联系人、电话、邮箱..."
            clearable
            @input="handleSearch"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </el-col>
        <el-col :span="2">
          <el-button @click="handleReset" plain>重置</el-button>
        </el-col>
      </el-row>
    </div>

    <el-table :data="suppliers" style="width: 100%" v-loading="loading" :default-sort="{ prop: 'id', order: 'descending' }">
      <el-table-column prop="id" label="ID" width="70" sortable />
      <el-table-column prop="name" label="供应商名称" min-width="150" show-overflow-tooltip />
      <el-table-column prop="contact" label="联系人" width="100" show-overflow-tooltip />
      <el-table-column prop="phone" label="电话" width="120" />
      <el-table-column prop="email" label="邮箱" width="180" show-overflow-tooltip />
      <el-table-column prop="address" label="地址" min-width="150" show-overflow-tooltip />
      <el-table-column prop="remark" label="备注" min-width="120" show-overflow-tooltip />
      <el-table-column label="操作" width="120" fixed="right">
        <template #default="{ row }">
          <el-button size="small" link @click="handleEdit(row)">编辑</el-button>
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

    <el-dialog v-model="dialogVisible" :title="dialogTitle" width="600px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="供应商名称" prop="name">
          <el-input v-model="form.name" placeholder="请输入供应商名称" />
        </el-form-item>
        <el-form-item label="联系人" prop="contact">
          <el-input v-model="form.contact" placeholder="请输入联系人" />
        </el-form-item>
        <el-form-item label="电话" prop="phone">
          <el-input v-model="form.phone" placeholder="请输入电话" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-input v-model="form.email" placeholder="请输入邮箱" />
        </el-form-item>
        <el-form-item label="地址" prop="address">
          <el-input v-model="form.address" type="textarea" :rows="2" placeholder="请输入地址" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model="form.remark" type="textarea" :rows="2" placeholder="请输入备注" />
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

const suppliers = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const dialogTitle = ref('新增供应商')
const formRef = ref(null)
const editingId = ref(null)

// 分页相关
const total = ref(0)
const currentPage = ref(1)
const pageSize = ref(15)

const form = reactive({
  name: '',
  contact: '',
  phone: '',
  email: '',
  address: '',
  remark: ''
})

const searchForm = reactive({
  search: ''
})

const rules = {
  name: [{ required: true, message: '请输入供应商名称', trigger: 'blur' }]
}

const getSearchParams = () => {
  const params = {}
  if (searchForm.search) params.search = searchForm.search
  return params
}

const loadSuppliers = async (params = {}) => {
  loading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await api.get('/suppliers/', {
      params: {
        ...params,
        skip,
        limit: pageSize.value
      }
    })
    suppliers.value = response.data.items
    total.value = response.data.total
  } catch (error) {
    ElMessage.error('加载供应商列表失败')
  } finally {
    loading.value = false
  }
}

const handleSearch = () => {
  currentPage.value = 1
  loadSuppliers(getSearchParams())
}

const handleReset = () => {
  searchForm.search = ''
  currentPage.value = 1
  loadSuppliers()
}

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
  loadSuppliers(getSearchParams())
}

const handleCurrentChange = (val) => {
  currentPage.value = val
  loadSuppliers(getSearchParams())
}

const handleAdd = () => {
  editingId.value = null
  dialogTitle.value = '新增供应商'
  Object.assign(form, {
    name: '',
    contact: '',
    phone: '',
    email: '',
    address: '',
    remark: ''
  })
  dialogVisible.value = true
}

const handleEdit = (row) => {
  editingId.value = row.id
  dialogTitle.value = '编辑供应商'
  Object.assign(form, {
    name: row.name || '',
    contact: row.contact || '',
    phone: row.phone || '',
    email: row.email || '',
    address: row.address || '',
    remark: row.remark || ''
  })
  dialogVisible.value = true
}

const handleSubmit = async () => {
  await formRef.value.validate(async (valid) => {
    if (valid) {
      try {
        if (editingId.value) {
          await api.put(`/suppliers/${editingId.value}`, form)
          ElMessage.success('更新成功')
        } else {
          await api.post('/suppliers/', form)
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
    await ElMessageBox.confirm('确定要删除该供应商吗？', '提示', { type: 'warning' })
    await api.delete(`/suppliers/${row.id}`)
    ElMessage.success('删除成功')
    handleSearch()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

onMounted(() => {
  loadSuppliers()
})
</script>

<style scoped>
.suppliers-container {
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
</style>