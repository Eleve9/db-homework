from flask import Flask, render_template, request, redirect, url_for
import sqlite3

app = Flask(__name__)

DB_NAME = "database.db"

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/users')
def users():
    conn = get_conn()

    user_list = conn.execute("""
        SELECT * FROM user ORDER BY user_id
    """).fetchall()

    total_items = conn.execute("""
        SELECT COUNT(*) AS total_items FROM item
    """).fetchone()

    category_counts = conn.execute("""
        SELECT category, COUNT(*) AS cnt
        FROM item
        GROUP BY category
        ORDER BY category
    """).fetchall()

    avg_price = conn.execute("""
        SELECT AVG(price) AS avg_price FROM item
    """).fetchone()

    top_user = conn.execute("""
        SELECT u.user_id, u.user_name, COUNT(i.item_id) AS item_count
        FROM user u
        JOIN item i ON u.user_id = i.seller_id
        GROUP BY u.user_id, u.user_name
        ORDER BY item_count DESC, u.user_id ASC
        LIMIT 1
    """).fetchone()

    conn.close()

    return render_template(
        'users.html',
        users=user_list,
        total_items=total_items,
        category_counts=category_counts,
        avg_price=avg_price,
        top_user=top_user
    )

@app.route('/items')
def items():
    mode = request.args.get('mode', 'all')
    msg = request.args.get('msg', '')

    conn = get_conn()

    if mode == 'unsold':
        sql = "SELECT * FROM item WHERE status = 0 ORDER BY item_id"
        query_title = "查询结果：所有未售出的商品"
    elif mode == 'price_gt_30':
        sql = "SELECT * FROM item WHERE price > 30 ORDER BY item_id"
        query_title = "查询结果：价格大于 30 的商品"
    elif mode == 'daily_goods':
        sql = "SELECT * FROM item WHERE category = 'DailyGoods' ORDER BY item_id"
        query_title = "查询结果：生活用品类商品"
    elif mode == 'seller_u001':
        sql = "SELECT * FROM item WHERE seller_id = 'u001' ORDER BY item_id"
        query_title = "查询结果：u001 发布的所有商品"
    else:
        sql = "SELECT * FROM item ORDER BY item_id"
        query_title = "当前商品数据（全部）"

    item_list = conn.execute(sql).fetchall()
    conn.close()

    return render_template(
        'items.html',
        items=item_list,
        query_title=query_title,
        mode=mode,
        msg=msg
    )

@app.route('/orders')
def orders():
    mode = request.args.get('mode', 'all')
    conn = get_conn()

    if mode == 'sold_with_buyer':
        query_title = "查询结果：所有已售商品及其买家姓名"
        result_list = conn.execute("""
            SELECT i.item_id, i.item_name, u.user_name AS buyer_name
            FROM orders o
            JOIN item i ON o.item_id = i.item_id
            JOIN user u ON o.buyer_id = u.user_id
            WHERE i.status = 1
            ORDER BY i.item_id
        """).fetchall()
        template_mode = 'sold_with_buyer'

    elif mode == 'seller_u001_status':
        query_title = "查询结果：卖家是 u001 的商品是否被购买"
        result_list = conn.execute("""
            SELECT i.item_id, i.item_name,
                   CASE
                       WHEN o.item_id IS NOT NULL THEN '已购买'
                       ELSE '未购买'
                   END AS purchase_status
            FROM item i
            LEFT JOIN orders o ON i.item_id = o.item_id
            WHERE i.seller_id = 'u001'
            ORDER BY i.item_id
        """).fetchall()
        template_mode = 'seller_u001_status'

    else:
        query_title = "查询结果：每个订单（商品名 + 买家名 + 日期）"
        result_list = conn.execute("""
            SELECT o.order_id, i.item_name, u.user_name AS buyer_name, o.order_date
            FROM orders o
            JOIN item i ON o.item_id = i.item_id
            JOIN user u ON o.buyer_id = u.user_id
            ORDER BY o.order_id
        """).fetchall()
        template_mode = 'order_detail'

    sold_view = conn.execute("""
        SELECT * FROM sold_items_view
    """).fetchall()

    unsold_view = conn.execute("""
        SELECT * FROM unsold_items_view
    """).fetchall()

    conn.close()

    return render_template(
        'orders.html',
        results=result_list,
        query_title=query_title,
        mode=template_mode,
        sold_view=sold_view,
        unsold_view=unsold_view
    )

@app.route('/add_item', methods=['POST'])
def add_item():
    item_id = request.form['item_id']
    item_name = request.form['item_name']
    category = request.form['category']
    price = request.form['price']
    seller_id = request.form['seller_id']

    conn = get_conn()
    try:
        conn.execute("""
            INSERT INTO item (item_id, item_name, category, price, status, seller_id)
            VALUES (?, ?, ?, ?, 0, ?)
        """, (item_id, item_name, category, price, seller_id))
        conn.commit()
    except sqlite3.IntegrityError as e:
        conn.close()
        return f"添加失败：{e}<br><a href='/items'>返回商品页</a>"

    conn.close()
    return redirect(url_for('items'))

@app.route('/update_price', methods=['POST'])
def update_price():
    item_id = request.form['item_id']
    new_price = request.form['new_price']

    conn = get_conn()
    conn.execute("""
        UPDATE item
        SET price = ?
        WHERE item_id = ?
    """, (new_price, item_id))
    conn.commit()
    conn.close()

    return redirect(url_for('items'))

@app.route('/delete_item', methods=['POST'])
def delete_item():
    item_id = request.form['item_id']

    conn = get_conn()
    conn.execute("""
        DELETE FROM item
        WHERE item_id = ? AND status = 0
    """, (item_id,))
    conn.commit()
    conn.close()

    return redirect(url_for('items'))

@app.route('/buy_item', methods=['POST'])
def buy_item():
    order_id = request.form['order_id']
    item_id = request.form['item_id']
    buyer_id = request.form['buyer_id']
    order_date = request.form['order_date']

    conn = get_conn()

    try:
        conn.execute("BEGIN IMMEDIATE")

        cur = conn.execute("""
            UPDATE item
            SET status = 1
            WHERE item_id = ? AND status = 0
        """, (item_id,))

        if cur.rowcount == 0:
            conn.rollback()
            conn.close()
            return redirect(url_for('items', msg='购买失败：该商品不存在或已经售出'))

        conn.execute("""
            INSERT INTO orders (order_id, item_id, buyer_id, order_date)
            VALUES (?, ?, ?, ?)
        """, (order_id, item_id, buyer_id, order_date))

        conn.commit()
        conn.close()
        return redirect(url_for('items', msg='购买成功：订单已生成，商品状态已更新为已售出'))

    except sqlite3.IntegrityError as e:
        conn.rollback()
        conn.close()
        return redirect(url_for('items', msg=f'购买失败：{e}'))

    except Exception as e:
        conn.rollback()
        conn.close()
        return redirect(url_for('items', msg=f'购买失败：{e}'))

if __name__ == '__main__':
    app.run(debug=True)