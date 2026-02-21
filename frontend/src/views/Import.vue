<template>
  <div>
    <h2>Excel导入</h2>
    
    <el-card style="margin-top: 20px">
      <el-upload
        ref="uploadRef"
        :auto-upload="false"
        :on-change="handleFileChange"
        :file-list="fileList"
        accept=".xlsx,.xls"
        drag
      >
        <el-icon class="el-icon--upload"><upload-filled /></el-icon>
        <div class="el-upload__text">
          将文件拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 .xlsx 和 .xls 格式，必须包含两个sheet：销售订单明细、库存记录
          </div>
        </template>
      </el-upload>
      
      <div style="margin-top: 20px">
        <el-checkbox v-model="skipErrors">跳过错误数据继续导入</el-checkbox>
        <el-button type="primary" @click="handleImport" :loading="importing" style="margin-left: 20px">
          开始导入
        </el-button>
      </div>
    </el-card>

    <el-card v-if="importResult" style="margin-top: 20px">
      <h3>导入结果</h3>
      <el-alert
        :type="importResult.success ? 'success' : 'warning'"
        :title="`导入完成：成功 ${importResult.success_rows} 条，失败 ${importResult.error_rows} 条`"
        :closable="false"
        style="margin-bottom: 20px"
      />
      
      <div v-if="importResult.errors.length > 0">
        <h4>错误详情</h4>
        <el-table :data="importResult.errors" style="width: 100%" max-height="400">
          <el-table-column prop="error_type" label="错误类型" width="150" />
          <el-table-column prop="error_message" label="错误信息" show-overflow-tooltip />
          <el-table-column prop="created_at" label="时间" width="180">
            <template #default="{ row }">
              {{ formatDate(row.created_at) }}
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import api from '../api'
import dayjs from 'dayjs'

const uploadRef = ref(null)
const fileList = ref([])
const skipErrors = ref(false)
const importing = ref(false)
const importResult = ref(null)

const formatDate = (date) => {
  return dayjs(date).format('YYYY-MM-DD HH:mm:ss')
}

const handleFileChange = (file) => {
  fileList.value = [file]
}

const handleImport = async () => {
  if (fileList.value.length === 0) {
    ElMessage.warning('请先选择文件')
    return
  }
  
  importing.value = true
  try {
    const formData = new FormData()
    formData.append('file', fileList.value[0].raw)
    
    const response = await api.post('/import/excel', formData, {
      params: { skip_errors: skipErrors.value },
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
    
    importResult.value = response.data
    
    if (response.data.error_rows > 0) {
      ElMessage.warning(`导入完成，但有 ${response.data.error_rows} 条错误`)
    } else {
      ElMessage.success('导入成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '导入失败')
  } finally {
    importing.value = false
  }
}
</script>
