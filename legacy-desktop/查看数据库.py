# -*- coding: utf-8 -*-
"""
查看护动智眸数据库内容
不需要安装任何额外软件，直接运行即可
"""

import subprocess
import sys

# 检查是否有 mysql-connector-python
try:
    import mysql.connector
except ImportError:
    print("正在安装 mysql-connector-python...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python", "-q"])
    import mysql.connector

def show_table(conn, table_name):
    print(f"\n{'='*60}")
    print(f"表：{table_name}")
    print('='*60)
    
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 50")
    rows = cursor.fetchall()
    
    if not rows:
        print("(空表，没有数据)")
        return
    
    # 打印表头
    headers = list(rows[0].keys())
    print(" | ".join(headers))
    print("-" * 60)
    
    # 打印数据
    for row in rows:
        values = []
        for h in headers:
            v = row[h]
            if v is None:
                values.append("NULL")
            elif isinstance(v, bytes):
                values.append(v.decode('utf-8', errors='ignore')[:20])
            else:
                values.append(str(v)[:30])
        print(" | ".join(values))
    
    cursor.close()

try:
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="hudong2024",
        database="hudongzhimou",
        port=3306,
        charset='utf8mb4'
    )
    
    print("✅ 连接成功！")
    
    # 查看所有表
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [t[0] for t in cursor.fetchall()]
    cursor.close()
    
    print(f"\n数据库中有 {len(tables)} 张表: {', '.join(tables)}")
    
    for table in tables:
        show_table(conn, table)
    
    conn.close()
    print("\n✅ 查询完成")
    
except Exception as e:
    print(f"❌ 出错: {e}")
    print("\n请确认：")
    print("1. MySQL 是否已经启动？")
    print("2. 密码是否正确？（默认是 hudong2024）")
    print("3. 数据库 hudongzhimou 是否已经创建？")

input("\n按回车键退出...")
