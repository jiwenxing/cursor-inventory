"""
初始化数据库脚本
创建管理员账号
"""
from app.database import SessionLocal, engine, Base
from app.models import User
from app.utils import get_password_hash

def init_db():
    """初始化数据库"""
    # 创建所有表
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        # 检查是否已有管理员
        admin = db.query(User).filter(User.username == "admin").first()
        if not admin:
            admin = User(
                username="admin",
                password_hash=get_password_hash("admin123"),
                name="管理员"
            )
            db.add(admin)
            db.commit()
            print("✓ 管理员账号创建成功：用户名=admin, 密码=admin123")
        else:
            print("✓ 管理员账号已存在")
    except Exception as e:
        print(f"✗ 初始化失败：{e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
