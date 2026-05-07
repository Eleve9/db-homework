import os
import sqlite3

DB_NAME = "database.db"

# 如果数据库已经存在，先删掉，重新创建
if os.path.exists(DB_NAME):
    os.remove(DB_NAME)

conn = sqlite3.connect(DB_NAME)
conn.execute("PRAGMA foreign_keys = ON;")
cur = conn.cursor()

cur.executescript("""
CREATE TABLE user (
    user_id TEXT PRIMARY KEY,
    user_name TEXT NOT NULL,
    phone TEXT NOT NULL
);

CREATE TABLE item (
    item_id TEXT PRIMARY KEY,
    item_name TEXT NOT NULL,
    category TEXT NOT NULL,
    price REAL NOT NULL CHECK(price >= 0),
    status INTEGER NOT NULL CHECK(status IN (0, 1)),
    seller_id TEXT NOT NULL,
    FOREIGN KEY (seller_id) REFERENCES user(user_id)
);

CREATE TABLE orders (
    order_id TEXT PRIMARY KEY,
    item_id TEXT NOT NULL UNIQUE,
    buyer_id TEXT NOT NULL,
    order_date TEXT NOT NULL,
    FOREIGN KEY (item_id) REFERENCES item(item_id),
    FOREIGN KEY (buyer_id) REFERENCES user(user_id)
);

INSERT INTO user (user_id, user_name, phone) VALUES
('u001', 'ZhangSan', '13800000001'),
('u002', 'LiSi', '13800000002'),
('u003', 'WangWu', '13800000003'),
('u004', 'ZhaoLiu', '13800000004');

INSERT INTO item (item_id, item_name, category, price, status, seller_id) VALUES
('i001', 'CalculusBook', 'Book', 20, 0, 'u001'),
('i002', 'DeskLamp', 'DailyGoods', 35, 1, 'u002'),
('i003', 'Microcontroller', 'Electronics', 80, 0, 'u001'),
('i004', 'Chair', 'Furniture', 50, 1, 'u003'),
('i005', 'WaterBottle', 'DailyGoods', 15, 0, 'u004');

INSERT INTO orders (order_id, item_id, buyer_id, order_date) VALUES
('o001', 'i002', 'u001', '2024-05-01'),
('o002', 'i004', 'u002', '2024-05-03');

CREATE VIEW sold_items_view AS
SELECT i.item_name, o.buyer_id
FROM item i
JOIN orders o ON i.item_id = o.item_id
WHERE i.status = 1;

CREATE VIEW unsold_items_view AS
SELECT item_id, item_name, category, price, seller_id
FROM item
WHERE status = 0;
""")

conn.commit()

print("database.db 创建成功")
print()

print("user 表数据：")
for row in cur.execute("SELECT * FROM user"):
    print(row)

print()
print("item 表数据：")
for row in cur.execute("SELECT * FROM item"):
    print(row)

print()
print("orders 表数据：")
for row in cur.execute("SELECT * FROM orders"):
    print(row)

conn.close()