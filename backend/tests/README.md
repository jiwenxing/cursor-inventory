# Excel导入功能测试说明

## 测试覆盖范围

### 1. 字段映射测试 (`TestColumnMapping`)
- ✅ 列名标准化功能
- ✅ 列名查找功能（支持多种变体）
- ✅ 列名变体处理（中英文括号等）

### 2. 金额计算测试 (`TestDecimalRounding`)
- ✅ 四舍五入功能

### 3. 异常检测测试 (`TestErrorDetection`)
- ✅ 缺失字段检测（型号、客户、数量）
- ✅ 金额计算错误检测
- ✅ 发货数量异常检测
- ✅ 品牌冲突检测

### 4. 订单级别异常检测 (`TestOrderErrorDetection`)
- ✅ 合同金额与订单行金额汇总不一致检测

### 5. Excel文件读取测试 (`TestExcelFileReading`)
- ✅ xlsx文件读取
- ✅ xls文件读取（如果xlrd可用）
- ✅ 文件格式检测（文件头识别）

### 6. 真实文件测试 (`TestRealExcelFile`)
- ⚠️ demo.xlsx文件读取（如果文件存在且格式正确）
- ⚠️ demo文件字段映射测试

## 运行测试

### 方式一：使用测试脚本
```bash
cd backend
./run_tests.sh
```

### 方式二：直接使用pytest
```bash
cd backend
source venv/bin/activate
pytest tests/test_excel_import.py -v
```

### 方式三：运行特定测试类
```bash
# 只运行字段映射测试
pytest tests/test_excel_import.py::TestColumnMapping -v

# 只运行异常检测测试
pytest tests/test_excel_import.py::TestErrorDetection -v

# 只运行真实文件测试
pytest tests/test_excel_import.py::TestRealExcelFile -v -s
```

## 测试结果

当前测试状态：
- ✅ **11个测试通过**
- ⚠️ **3个测试跳过**（xls文件写入测试、demo文件测试）

## 测试数据

测试使用以下数据：
- 内存中创建的测试Excel文件（xlsx格式）
- 真实的demo.xlsx文件（如果存在）

## 注意事项

1. **xlrd依赖**：某些测试需要xlrd库来读取.xls格式文件
2. **demo.xlsx文件**：真实文件测试需要项目根目录下的demo.xlsx文件
3. **文件格式**：如果demo.xlsx实际是.xls格式但扩展名是.xlsx，测试会自动尝试多个引擎

## 添加新测试

在 `test_excel_import.py` 中添加新的测试类或测试方法：

```python
class TestNewFeature:
    def test_something(self):
        # 测试代码
        assert True
```

## 测试覆盖率

当前测试覆盖：
- ✅ 字段映射逻辑
- ✅ 异常检测逻辑
- ✅ 文件格式识别
- ✅ Excel文件读取
- ⚠️ 完整导入流程（需要数据库和API测试）
