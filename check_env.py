#!/usr/bin/env python3
"""
环境检查脚本
检查Python版本和必要的依赖
"""
import sys
import subprocess

def check_python_version():
    """检查Python版本"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 11):
        print("❌ Python版本过低，需要Python 3.11+")
        print(f"   当前版本: {version.major}.{version.minor}.{version.micro}")
        return False
    else:
        print(f"✅ Python版本: {version.major}.{version.minor}.{version.micro}")
        return True

def check_node():
    """检查Node.js"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js: {result.stdout.strip()}")
            return True
        else:
            print("❌ Node.js未安装")
            return False
    except FileNotFoundError:
        print("❌ Node.js未安装")
        return False

def check_npm():
    """检查npm"""
    try:
        result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ npm: {result.stdout.strip()}")
            return True
        else:
            print("❌ npm未安装")
            return False
    except FileNotFoundError:
        print("❌ npm未安装")
        return False

def main():
    print("=" * 50)
    print("环境检查")
    print("=" * 50)
    
    python_ok = check_python_version()
    node_ok = check_node()
    npm_ok = check_npm()
    
    print("\n" + "=" * 50)
    if python_ok and node_ok and npm_ok:
        print("✅ 环境检查通过！可以开始启动项目")
        print("\n下一步：")
        print("1. 后端: cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt")
        print("2. 前端: cd frontend && npm install")
    else:
        print("❌ 环境检查未通过，请先安装缺失的依赖")
    print("=" * 50)

if __name__ == "__main__":
    main()
