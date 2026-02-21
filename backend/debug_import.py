#!/usr/bin/env python3
"""
调试Excel导入功能
直接测试文件读取和字段映射
"""
import sys
import os
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

import pandas as pd
from app.api.import_excel import find_column, normalize_column_name

def debug_excel_file(file_path):
    """调试Excel文件"""
    print("=" * 60)
    print(f"调试文件: {file_path}")
    print("=" * 60)
    
    if not os.path.exists(file_path):
        print(f"❌ 文件不存在: {file_path}")
        return
    
    # 检测文件格式
    with open(file_path, 'rb') as f:
        header = f.read(8)
    
    print(f"\n文件头: {header.hex()}")
    
    # 根据文件头选择引擎
    if header[:2] == b'PK':
        engine = 'openpyxl'
        print("✓ 检测为xlsx格式（zip）")
    elif header[:8] == b'\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1':
        engine = 'xlrd'
        print("✓ 检测为xls格式（OLE）")
    else:
        print("⚠️ 无法识别的格式，尝试openpyxl")
        engine = 'openpyxl'
    
    # 尝试读取
    try:
        print(f"\n尝试使用 {engine} 引擎读取...")
        df1 = pd.read_excel(file_path, sheet_name=0, engine=engine, nrows=10)
        print(f"✓ Sheet1读取成功")
        print(f"  行数: {len(df1)}")
        print(f"  列名: {list(df1.columns)}")
        print(f"\n前5行数据:")
        print(df1.head().to_string())
        
        # 测试字段映射
        print("\n" + "=" * 60)
        print("字段映射测试")
        print("=" * 60)
        
        col_mapping = {
            'order_no': find_column(df1, ['订单号', '订单编号', 'order_no']),
            'order_date': find_column(df1, ['订单日期', '日期', 'order_date']),
            'customer': find_column(df1, ['客户', '客户名称', 'customer']),
            'model': find_column(df1, ['型号', '产品型号', 'model']),
            'quantity': find_column(df1, ['数量', 'quantity']),
        }
        
        print("\n映射结果:")
        for key, value in col_mapping.items():
            status = "✓" if value in df1.columns else "✗"
            print(f"  {status} {key}: {value}")
        
        # 检查必需字段
        required = ['model', 'customer', 'quantity']
        missing = [f for f in required if col_mapping[f] not in df1.columns]
        
        if missing:
            print(f"\n❌ 缺少必需字段: {missing}")
        else:
            print(f"\n✓ 所有必需字段都已找到")
        
        # 读取Sheet2
        try:
            df2 = pd.read_excel(file_path, sheet_name=1, engine=engine, nrows=10)
            print(f"\n✓ Sheet2读取成功")
            print(f"  行数: {len(df2)}")
            print(f"  列名: {list(df2.columns)}")
        except Exception as e:
            print(f"\n❌ Sheet2读取失败: {e}")
            
    except Exception as e:
        print(f"\n❌ 读取失败: {e}")
        import traceback
        traceback.print_exc()
        
        # 尝试另一个引擎
        if engine == 'openpyxl':
            print("\n尝试使用xlrd引擎...")
            try:
                df1 = pd.read_excel(file_path, sheet_name=0, engine='xlrd', nrows=10)
                print("✓ 使用xlrd成功读取")
                print(f"列名: {list(df1.columns)}")
            except Exception as e2:
                print(f"❌ xlrd也失败: {e2}")
        else:
            print("\n尝试使用openpyxl引擎...")
            try:
                df1 = pd.read_excel(file_path, sheet_name=0, engine='openpyxl', nrows=10)
                print("✓ 使用openpyxl成功读取")
                print(f"列名: {list(df1.columns)}")
            except Exception as e2:
                print(f"❌ openpyxl也失败: {e2}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    else:
        # 默认使用demo.xlsx
        file_path = '../demo.xlsx'
    
    debug_excel_file(file_path)
