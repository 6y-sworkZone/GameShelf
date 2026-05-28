#!/usr/bin/env python
"""
数据库迁移执行脚本

用法:
    python migrate.py              # 执行所有未执行的迁移
    python migrate.py --status     # 查看迁移状态
    python migrate.py --list       # 列出所有迁移脚本
"""
import os
import sys
import importlib

MIGRATIONS_DIR = os.path.join(os.path.dirname(__file__), "migrations")


def get_migration_scripts():
    scripts = []
    for filename in sorted(os.listdir(MIGRATIONS_DIR)):
        if filename.endswith(".py") and filename != "__init__.py":
            scripts.append(filename)
    return scripts


def run_migration(script_name):
    module_name = f"migrations.{script_name[:-3]}"
    try:
        module = importlib.import_module(module_name)
        if hasattr(module, "upgrade"):
            module.upgrade()
            return True
        else:
            print(f"⚠️  迁移脚本 {script_name} 没有 upgrade() 函数")
            return False
    except Exception as e:
        print(f"❌ 执行迁移 {script_name} 失败: {e}")
        return False


def show_status():
    print("\n📋 迁移脚本列表:\n")
    for script in get_migration_scripts():
        print(f"  • {script}")
    print()


def main():
    if len(sys.argv) > 1:
        if sys.argv[1] in ("--status", "--list"):
            show_status()
            return
        elif sys.argv[1] == "--help":
            print(__doc__)
            return

    print("🚀 开始执行数据库迁移...\n")

    scripts = get_migration_scripts()
    success_count = 0

    for script in scripts:
        if run_migration(script):
            success_count += 1

    print(f"\n✅ 迁移完成: 成功 {success_count}/{len(scripts)} 个")


if __name__ == "__main__":
    main()
