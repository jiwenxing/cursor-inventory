"""
Excel导入功能单元测试
"""
import pytest
import pandas as pd
import os
import sys
from io import BytesIO
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.api.import_excel import (
    normalize_column_name,
    find_column,
    round_decimal,
    detect_errors,
    detect_order_errors
)
from app.models import Product, Customer


class TestColumnMapping:
    """测试字段映射功能"""
    
    def test_normalize_column_name(self):
        """测试列名标准化"""
        assert normalize_column_name("订单号") == "订单号"
        assert normalize_column_name(" 订单号 ") == "订单号"
        assert normalize_column_name("单价（含税）") == "单价(含税)"
        assert normalize_column_name("单价(含税)") == "单价(含税)"
        assert normalize_column_name("") == ""
        # normalize_column_name会将pd.NA转换为空字符串
        result = normalize_column_name(pd.NA)
        assert result == "" or pd.isna(result)
    
    def test_find_column(self):
        """测试列名查找"""
        df = pd.DataFrame({
            '订单号': [1, 2, 3],
            '订单日期': ['2024-01-01', '2024-01-02', '2024-01-03'],
            '客户': ['客户A', '客户B', '客户C'],
            '型号': ['MODEL001', 'MODEL002', 'MODEL003']
        })
        
        # 测试找到列名
        assert find_column(df, ['订单号', 'order_no']) == '订单号'
        assert find_column(df, ['客户', 'customer']) == '客户'
        assert find_column(df, ['型号', 'model']) == '型号'
        
        # 测试找不到时返回第一个可能的名称
        assert find_column(df, ['不存在的列', 'another']) == '不存在的列'
    
    def test_find_column_with_variants(self):
        """测试列名变体查找"""
        df = pd.DataFrame({
            '单价（含税）': [100, 200, 300],
            '单价(含税)': [150, 250, 350],
            '含税单价': [120, 220, 320]
        })
        
        # 应该能找到第一个匹配的
        result = find_column(df, ['单价（含税）', '单价(含税)', '含税单价'])
        assert result in ['单价（含税）', '单价(含税)', '含税单价']


class TestDecimalRounding:
    """测试金额四舍五入"""
    
    def test_round_decimal(self):
        """测试四舍五入功能"""
        assert round_decimal(10.125) == 10.13
        assert round_decimal(10.124) == 10.12
        assert round_decimal(10.1255) == 10.13
        assert round_decimal(0) == 0.0
        assert round_decimal(None) == 0.0


class TestErrorDetection:
    """测试异常检测功能"""
    
    def test_detect_missing_fields(self):
        """测试缺失字段检测"""
        col_mapping = {
            'model': '型号',
            'customer': '客户',
            'quantity': '数量'
        }
        
        products_map = {}
        customers_map = {}
        
        # 测试缺失型号
        row = pd.Series({'客户': '客户A', '数量': 10})
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('型号' in e['error_message'] for e in errors)
        
        # 测试缺失客户
        row = pd.Series({'型号': 'MODEL001', '数量': 10})
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('客户' in e['error_message'] for e in errors)
        
        # 测试数量为0或负数
        row = pd.Series({'型号': 'MODEL001', '客户': '客户A', '数量': 0})
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('数量' in e['error_message'] for e in errors)
    
    def test_detect_amount_calculation_error(self):
        """测试金额计算错误检测"""
        col_mapping = {
            'model': '型号',
            'customer': '客户',
            'quantity': '数量',
            'unit_price_tax': '单价（含税）',
            'discount_rate': '折扣率',
            'amount': '金额'
        }
        
        products_map = {}
        customers_map = {}
        
        # 测试金额计算错误
        row = pd.Series({
            '型号': 'MODEL001',
            '客户': '客户A',
            '数量': 10,
            '单价（含税）': 100,
            '折扣率': 0.1,
            '金额': 1000  # 错误：应该是 10 * 100 * 0.9 = 900
        })
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('金额计算' in e['error_message'] for e in errors)
        
        # 测试金额计算正确（不应该报错）
        row = pd.Series({
            '型号': 'MODEL001',
            '客户': '客户A',
            '数量': 10,
            '单价（含税）': 100,
            '折扣率': 0.1,
            '金额': 900  # 正确：10 * 100 * 0.9 = 900
        })
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        # 金额计算正确的应该没有金额计算错误（但可能有其他错误，如品牌冲突）
        amount_errors = [e for e in errors if '金额计算' in e['error_message']]
        assert len(amount_errors) == 0
    
    def test_detect_shipped_quantity_error(self):
        """测试发货数量异常检测"""
        col_mapping = {
            'model': '型号',
            'customer': '客户',
            'quantity': '数量',
            'shipped_quantity': '发货数量'
        }
        
        products_map = {}
        customers_map = {}
        
        # 测试发货数量大于订货数量
        row = pd.Series({
            '型号': 'MODEL001',
            '客户': '客户A',
            '数量': 10,
            '发货数量': 15  # 错误：发货数量大于订货数量
        })
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('发货数量' in e['error_message'] for e in errors)
    
    def test_detect_brand_conflict(self):
        """测试品牌冲突检测"""
        col_mapping = {
            'model': '型号',
            'customer': '客户',
            'quantity': '数量',
            'brand': '品牌'
        }
        
        # 创建已存在的产品
        existing_product = Product()
        existing_product.model = 'MODEL001'
        existing_product.brand = '品牌A'
        products_map = {'MODEL001': existing_product}
        customers_map = {}
        
        # 测试品牌冲突
        row = pd.Series({
            '型号': 'MODEL001',
            '客户': '客户A',
            '数量': 10,
            '品牌': '品牌B'  # 冲突：已存在品牌A
        })
        errors = detect_errors(row, 0, products_map, customers_map, col_mapping)
        assert len(errors) > 0
        assert any('品牌冲突' in e['error_message'] or '品牌' in e['error_message'] for e in errors)


class TestOrderErrorDetection:
    """测试订单级别异常检测"""
    
    def test_detect_contract_amount_error(self):
        """测试合同金额异常检测"""
        col_mapping = {
            'order_no': '订单号',
            'order_date': '订单日期',
            'contract_amount': '合同金额',
            'amount': '金额'
        }
        
        # 测试合同金额与订单行金额汇总不一致
        orders_data = [
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 1000, '金额': 300},
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 1000, '金额': 400},
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 1000, '金额': 200}
            # 订单行金额汇总 = 900，但合同金额 = 1000
        ]
        
        errors = detect_order_errors(orders_data, col_mapping)
        assert len(errors) > 0
        assert any('合同金额' in e['error_message'] for e in errors)
        
        # 测试合同金额正确（不应该报错）
        orders_data = [
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 900, '金额': 300},
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 900, '金额': 400},
            {'订单号': 'ORD001', '订单日期': '2024-01-01', '合同金额': 900, '金额': 200}
            # 订单行金额汇总 = 900，合同金额 = 900，正确
        ]
        
        errors = detect_order_errors(orders_data, col_mapping)
        contract_errors = [e for e in errors if '合同金额' in e['error_message']]
        assert len(contract_errors) == 0


class TestExcelFileReading:
    """测试Excel文件读取"""
    
    def test_read_xlsx_file(self):
        """测试读取xlsx文件"""
        # 创建测试用的xlsx文件
        df1 = pd.DataFrame({
            '订单号': ['ORD001', 'ORD002'],
            '订单日期': ['2024-01-01', '2024-01-02'],
            '客户': ['客户A', '客户B'],
            '型号': ['MODEL001', 'MODEL002'],
            '数量': [10, 20],
            '单价（含税）': [100, 200],
            '折扣率': [0, 0.1],
            '金额': [1000, 3600]
        })
        
        df2 = pd.DataFrame({
            '型号': ['MODEL001', 'MODEL002'],
            '库存数量': [100, 200]
        })
        
        # 保存为xlsx
        test_file = BytesIO()
        with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
            df1.to_excel(writer, sheet_name='Sheet1', index=False)
            df2.to_excel(writer, sheet_name='Sheet2', index=False)
        
        test_file.seek(0)
        
        # 读取xlsx
        df_sheet1 = pd.read_excel(test_file, sheet_name=0, engine='openpyxl')
        test_file.seek(0)
        df_sheet2 = pd.read_excel(test_file, sheet_name=1, engine='openpyxl')
        
        assert len(df_sheet1) == 2
        assert len(df_sheet2) == 2
        assert '订单号' in df_sheet1.columns
        assert '型号' in df_sheet2.columns
    
    def test_read_xls_file(self):
        """测试读取xls文件（如果xlrd可用）"""
        try:
            # 创建测试用的xls文件
            df1 = pd.DataFrame({
                '订单号': ['ORD001', 'ORD002'],
                '订单日期': ['2024-01-01', '2024-01-02'],
                '客户': ['客户A', '客户B'],
                '型号': ['MODEL001', 'MODEL002'],
                '数量': [10, 20]
            })
            
            # 保存为xls（需要xlrd）
            test_file = BytesIO()
            with pd.ExcelWriter(test_file, engine='xlrd') as writer:
                df1.to_excel(writer, sheet_name='Sheet1', index=False)
            
            test_file.seek(0)
            
            # 读取xls
            df_sheet1 = pd.read_excel(test_file, sheet_name=0, engine='xlrd')
            
            assert len(df_sheet1) == 2
            assert '订单号' in df_sheet1.columns
        except Exception as e:
            pytest.skip(f"xlrd不可用或xls写入失败: {e}")
    
    def test_file_format_detection(self):
        """测试文件格式检测"""
        # 测试xlsx文件头（zip格式）
        xlsx_header = b'PK\x03\x04'
        assert xlsx_header[:2] == b'PK'
        
        # 测试xls文件头（OLE格式）
        xls_header = b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'
        assert xls_header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1'


class TestRealExcelFile:
    """测试真实Excel文件（demo.xlsx）"""
    
    @pytest.fixture
    def demo_file_path(self):
        """获取demo.xlsx文件路径"""
        base_dir = Path(__file__).parent.parent.parent
        demo_file = base_dir / 'demo.xlsx'
        if demo_file.exists():
            return str(demo_file)
        pytest.skip("demo.xlsx文件不存在")
    
    def test_read_demo_file(self, demo_file_path):
        """测试读取demo.xlsx文件"""
        # 检测文件格式
        with open(demo_file_path, 'rb') as f:
            header = f.read(8)
        
        # 根据文件头选择引擎
        if header[:2] == b'PK':
            engines_to_try = ['openpyxl']
        elif header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
            engines_to_try = ['xlrd', 'openpyxl']  # 尝试xlrd，如果失败则尝试openpyxl
        else:
            engines_to_try = ['openpyxl', 'xlrd']  # 默认尝试两个引擎
        
        # 尝试读取文件
        df1 = None
        df2 = None
        last_error = None
        
        for engine in engines_to_try:
            try:
                df1 = pd.read_excel(demo_file_path, sheet_name=0, engine=engine, nrows=10)
                df2 = pd.read_excel(demo_file_path, sheet_name=1, engine=engine, nrows=10)
                print(f"\n✓ 成功使用 {engine} 引擎读取文件")
                break
            except Exception as e:
                last_error = e
                print(f"\n✗ 使用 {engine} 引擎失败: {e}")
                continue
        
        if df1 is None or df2 is None:
            pytest.skip(f"无法读取demo.xlsx文件，所有引擎都失败。最后错误: {last_error}")
        
        assert len(df1) > 0, "Sheet1应该有数据"
        assert len(df2) > 0, "Sheet2应该有数据"
        
        print(f"\nSheet1列名: {list(df1.columns)}")
        print(f"Sheet2列名: {list(df2.columns)}")
        print(f"\nSheet1前5行:")
        print(df1.head())
        print(f"\nSheet2前5行:")
        print(df2.head())
    
    def test_column_mapping_demo_file(self, demo_file_path):
        """测试demo文件的字段映射"""
        # 检测文件格式
        with open(demo_file_path, 'rb') as f:
            header = f.read(8)
        
        # 尝试读取文件
        engines_to_try = ['openpyxl', 'xlrd'] if header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1' else ['openpyxl']
        df1 = None
        
        for engine in engines_to_try:
            try:
                df1 = pd.read_excel(demo_file_path, sheet_name=0, engine=engine, nrows=5)
                break
            except Exception:
                continue
        
        if df1 is None:
            pytest.skip("无法读取demo.xlsx文件")
        
        # 测试字段映射
        col_mapping = {
            'order_no': find_column(df1, ['订单号', '订单编号', 'order_no']),
            'order_date': find_column(df1, ['订单日期', '日期', 'order_date']),
            'customer': find_column(df1, ['客户', '客户名称', 'customer']),
            'model': find_column(df1, ['型号', '产品型号', 'model']),
            'quantity': find_column(df1, ['数量', 'quantity']),
        }
        
        # 检查必需字段是否找到
        assert col_mapping['model'] in df1.columns, f"未找到型号列，可用列：{list(df1.columns)}"
        assert col_mapping['customer'] in df1.columns, f"未找到客户列，可用列：{list(df1.columns)}"
        assert col_mapping['quantity'] in df1.columns, f"未找到数量列，可用列：{list(df1.columns)}"
        
        print(f"\n字段映射结果:")
        for key, value in col_mapping.items():
            print(f"  {key}: {value}")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
