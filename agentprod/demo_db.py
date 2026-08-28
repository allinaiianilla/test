"""演示数据库初始化：一个小电商库，供 SQL 工具演示。"""
from __future__ import annotations

import json
import random
import sqlite3
from pathlib import Path

from .config import DATA_DIR

SCHEMA = """
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    vip_level INTEGER DEFAULT 0,
    created_at TEXT
);
CREATE TABLE products (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    category TEXT,
    price REAL,
    stock INTEGER
);
CREATE TABLE orders (
    id INTEGER PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    product_id INTEGER REFERENCES products(id),
    amount REAL,
    status TEXT CHECK(status IN ('paid','refunded','pending')),
    created_at TEXT
);
"""

CITIES = ["北京", "上海", "广州", "深圳", "杭州", "成都", "武汉", "西安"]
PRODUCTS = [
    ("机械键盘", "数码", 399.0), ("无线鼠标", "数码", 129.0),
    ("降噪耳机", "数码", 1299.0), ("显示器支架", "数码", 199.0),
    ("保温杯", "家居", 89.0), ("台灯", "家居", 159.0),
    ("人体工学椅", "家居", 1899.0), ("咖啡豆 1kg", "食品", 128.0),
    ("挂耳咖啡", "食品", 59.0), ("蛋白粉", "食品", 329.0),
]
NAMES = ["张伟", "王芳", "李娜", "刘洋", "陈静", "杨帆", "赵磊", "黄敏",
         "周涛", "吴倩", "徐强", "孙丽", "马超", "朱琳", "胡军", "郭婷",
         "何鑫", "高远", "林悦", "罗凯"]


def init_demo_db(force: bool = False) -> Path:
    db = DATA_DIR / "demo.db"
    if db.exists() and not force:
        return db
    db.parent.mkdir(parents=True, exist_ok=True)
    if db.exists():
        db.unlink()
    conn = sqlite3.connect(db)
    try:
        conn.executescript(SCHEMA)
        rnd = random.Random(42)  # 固定种子，结果可复现
        users = []
        for i, name in enumerate(NAMES, 1):
            users.append((i, name, rnd.choice(CITIES), rnd.randint(0, 3),
                          f"2025-{rnd.randint(1,12):02d}-{rnd.randint(1,28):02d}"))
        conn.executemany("INSERT INTO users VALUES (?,?,?,?,?)", users)
        prods = [(i, n, c, p, rnd.randint(0, 500))
                 for i, (n, c, p) in enumerate(PRODUCTS, 1)]
        conn.executemany("INSERT INTO products VALUES (?,?,?,?,?)", prods)
        orders = []
        for oid in range(1, 121):
            uid = rnd.randint(1, len(NAMES))
            pid = rnd.randint(1, len(PRODUCTS))
            qty = rnd.randint(1, 3)
            price = PRODUCTS[pid - 1][2]
            status = rnd.choices(["paid", "refunded", "pending"],
                                 weights=[80, 8, 12])[0]
            orders.append((oid, uid, pid, round(price * qty, 2), status,
                           f"2026-{rnd.randint(1,8):02d}-{rnd.randint(1,28):02d}"))
        conn.executemany("INSERT INTO orders VALUES (?,?,?,?,?,?)", orders)
        conn.commit()
    finally:
        conn.close()
    return db


if __name__ == "__main__":
    p = init_demo_db(force=True)
    print(f"demo db ready: {p}")
