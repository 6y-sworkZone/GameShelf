"""
迁移脚本 001: 添加 share_token 字段到 wishlist 表
创建日期: 2024-05-28
说明: 为愿望单分享功能添加 share_token 字段，用于标识分享链接
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "gameshelf.db")

MIGRATION_NAME = "001_add_share_token"
MIGRATION_DESCRIPTION = "Add share_token column to wishlist table"


def upgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        cursor.execute("PRAGMA table_info(wishlist)")
        columns = [col[1] for col in cursor.fetchall()]

        if "share_token" not in columns:
            print(f"[{MIGRATION_NAME}] 正在添加 share_token 字段到 wishlist 表...")
            cursor.execute("ALTER TABLE wishlist ADD COLUMN share_token VARCHAR")
            conn.commit()
            print(f"[{MIGRATION_NAME}] ✅ 成功添加 share_token 字段")
        else:
            print(f"[{MIGRATION_NAME}] ℹ️  share_token 字段已存在，跳过迁移")

    except Exception as e:
        print(f"[{MIGRATION_NAME}] ❌ 迁移失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


def downgrade():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    try:
        print(f"[{MIGRATION_NAME}] 正在删除 share_token 字段...")
        cursor.execute("""
            CREATE TABLE wishlist_new AS
            SELECT id, name, platform, expected_price, expected_discount,
                   priority, current_price, store_url, lowest_price,
                   lowest_price_date, notes, created_at, updated_at
            FROM wishlist
        """)
        cursor.execute("DROP TABLE wishlist")
        cursor.execute("ALTER TABLE wishlist_new RENAME TO wishlist")
        conn.commit()
        print(f"[{MIGRATION_NAME}] ✅ 成功删除 share_token 字段")
    except Exception as e:
        print(f"[{MIGRATION_NAME}] ❌ 回滚失败: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "downgrade":
        downgrade()
    else:
        upgrade()
