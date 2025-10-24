import logging
import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, flash, g, jsonify
from datetime import datetime  # 顶部导入datetime模块

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')

# 数据库表结构 SQL 语句（直接写在 Python 中）
SCHEMA_SQL = """
DROP TABLE IF EXISTS test_types;
DROP TABLE IF EXISTS regions;
DROP TABLE IF EXISTS centres;
DROP TABLE IF EXISTS bookings;

CREATE TABLE test_types (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE regions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE centres (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    region_id INTEGER,  
    FOREIGN KEY (region_id) REFERENCES regions (id)
);

CREATE TABLE bookings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    licence_number TEXT NOT NULL,
    contact_name TEXT NOT NULL,
    contact_phone TEXT NOT NULL,
    test_type_id INTEGER NOT NULL,
    region_id INTEGER NOT NULL,
    centre_id INTEGER NOT NULL,
    available_time TEXT NOT NULL,
    email TEXT NOT NULL,
    card_number TEXT NOT NULL,
    expiry_month INTEGER NOT NULL, 
    expiry_year INTEGER NOT NULL,  
    data TEXT,                     
    cvn TEXT NOT NULL,
    FOREIGN KEY (test_type_id) REFERENCES test_types (id),
    FOREIGN KEY (region_id) REFERENCES regions (id),
    FOREIGN KEY (centre_id) REFERENCES centres (id)
);
"""


# 新增：根据地区ID获取中心列表（供前端AJAX调用）
@app.route('/api/centres-by-region')
def get_centres_by_region():
    region_id = request.args.get('region_id')
    if not region_id:
        return jsonify([])  # 未选择地区时返回空列表
    # 查询指定地区的中心
    centres = query_db('SELECT id, name FROM centres WHERE region_id = ? ORDER BY name', [region_id])
    # 转换为字典列表返回
    return jsonify([{'id': c['id'], 'name': c['name']} for c in centres])


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(app.config['DATABASE'])
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def init_db():
    with app.app_context():
        db = get_db()
        try:
            # 执行 SQL 语句
            db.cursor().executescript(SCHEMA_SQL)
            # 添加默认数据
            db.execute("INSERT INTO test_types (name) VALUES (?)", ["Class C/CA - Car"])
            db.execute("INSERT INTO regions (name) VALUES (?)", ["SEQ BRISBANE SOUTHSIDE"])
            db.commit()
            print("数据库初始化成功")
        except Exception as e:
            db.rollback()
            print(f"数据库初始化失败: {e}")


# app.py 新增接口
@app.route('/api/bookings')
def api_bookings():
    bookings = query_db('''
        SELECT b.*, tt.name as test_type_name, r.name as region_name, c.name as centre_name
        FROM bookings b
        JOIN test_types tt ON b.test_type_id = tt.id
        JOIN regions r ON b.region_id = r.id
        JOIN centres c ON b.centre_id = c.id
        ORDER BY b.id DESC
    ''')
    # 转换为字典列表
    data = [dict(booking) for booking in bookings]
    return jsonify({"rows": data, "total": len(data)})


def query_db(query, args=(), one=False):
    cur = get_db().execute(query, args)
    rv = cur.fetchall()
    cur.close()
    return (rv[0] if rv else None) if one else rv


def execute_db(query, args=()):
    try:
        db = get_db()
        cur = db.execute(query, args)
        db.commit()
        id = cur.lastrowid
        cur.close()
        return id
    except sqlite3.IntegrityError as e:
        db.rollback()
        flash(f'数据完整性错误: {str(e)}', 'danger')
        raise e
    except Exception as e:
        db.rollback()
        flash(f'数据库操作失败: {str(e)}', 'danger')
        raise e


@app.route('/')
def index():
    try:
        # 获取所有下拉框数据
        test_types = query_db('SELECT * FROM test_types ORDER BY name')
        regions = query_db('SELECT * FROM regions ORDER BY name')
        centres = query_db('SELECT * FROM centres ORDER BY name')

        # 获取所有预订记录，关联下拉框的名称
        bookings = query_db('''
            SELECT b.*, tt.name as test_type_name, r.name as region_name, c.name as centre_name
            FROM bookings b
            JOIN test_types tt ON b.test_type_id = tt.id
            JOIN regions r ON b.region_id = r.id
            JOIN centres c ON b.centre_id = c.id
            ORDER BY b.id DESC
        ''')

        return render_template('index.html',
                               bookings=bookings,
                               test_types=test_types,
                               regions=regions,
                               centres=centres)
    except Exception as e:
        flash(f'加载数据失败: {str(e)}', 'danger')
        return render_template('index.html',
                               bookings=[],
                               test_types=[],
                               regions=[],
                               centres=[])

    # 添加当前时间变量
    now = datetime.now()

    return render_template('index.html',
                           bookings=bookings,  # 现在该变量已定义
                           test_types=test_types,
                           regions=regions,
                           centres=centres)


# 下拉框数据管理
@app.route('/add-test-type', methods=['POST'])
def add_test_type():
    name = request.form['test_type'].strip()
    if name:
        try:
            execute_db('INSERT INTO test_types (name) VALUES (?)', [name])
            flash('测试类型添加成功', 'success')
        except sqlite3.IntegrityError:
            flash('该测试类型已存在', 'danger')
    return redirect(url_for('index'))


@app.route('/add-region', methods=['POST'])
def add_region():
    name = request.form['region'].strip()
    if name:
        try:
            execute_db('INSERT INTO regions (name) VALUES (?)', [name])
            flash('地区添加成功', 'success')
        except sqlite3.IntegrityError:
            flash('该地区已存在', 'danger')
    return redirect(url_for('index'))


@app.route('/add-centre', methods=['POST'])
def add_centre():
    name = request.form['centre'].strip()
    region_id = request.form['region_id']  # 获取关联的地区ID
    if name and region_id:
        try:
            execute_db('INSERT INTO centres (name, region_id) VALUES (?, ?)', [name, region_id])
            flash('中心添加成功', 'success')
        except sqlite3.IntegrityError:
            flash('该中心已存在', 'danger')
    else:
        flash('请填写中心名称并选择所属地区', 'danger')
    return redirect(url_for('index'))


@app.route('/delete-test-type/<int:id>', methods=['POST'])
def delete_test_type(id):
    # 检查是否有关联的预订记录
    bookings = query_db('SELECT id FROM bookings WHERE test_type_id = ?', [id])
    if bookings:
        flash('无法删除，该测试类型已被预订记录使用', 'danger')
        return redirect(url_for('index'))

    execute_db('DELETE FROM test_types WHERE id = ?', [id])
    flash('测试类型已删除', 'success')
    return redirect(url_for('index'))


@app.route('/delete-region/<int:id>', methods=['POST'])
def delete_region(id):
    # 检查是否有关联的预订记录
    bookings = query_db('SELECT id FROM bookings WHERE region_id = ?', [id])
    if bookings:
        flash('无法删除，该地区已被预订记录使用', 'danger')
        return redirect(url_for('index'))

    execute_db('DELETE FROM regions WHERE id = ?', [id])
    flash('地区已删除', 'success')
    return redirect(url_for('index'))


@app.route('/delete-centre/<int:id>', methods=['POST'])
def delete_centre(id):
    # 检查是否有关联的预订记录
    bookings = query_db('SELECT id FROM bookings WHERE centre_id = ?', [id])
    if bookings:
        flash('无法删除，该中心已被预订记录使用', 'danger')
        return redirect(url_for('index'))

    execute_db('DELETE FROM centres WHERE id = ?', [id])
    flash('中心已删除', 'success')
    return redirect(url_for('index'))


# 预订记录管理
@app.route('/add-booking', methods=['POST'])
def add_booking():
    data = request.form
    try:
        execute_db('''
            INSERT INTO bookings (
                licence_number, contact_name, contact_phone, test_type_id, region_id, 
                centre_id, available_time, email, card_number, expiry_month, expiry_year, data, cvn
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', [
            data['licence_number'],
            data['contact_name'],
            data['contact_phone'],
            data['test_type_id'],
            data['region_id'],
            data['centre_id'],
            data['available_time'],
            data['email'],
            data['card_number'],
            data['expiry_month'],  # 替换原expiry_date
            data['expiry_year'],  # 新增年份
            data['data'],
            data['cvn']
        ])
        flash('记录添加成功', 'success')
    except Exception as e:
        flash(f'添加失败: {str(e)}', 'danger')
    return redirect(url_for('index'))


@app.route('/update-booking/<int:id>', methods=['POST'])
def update_booking(id):
    data = request.form
    try:
        execute_db('''
            UPDATE bookings SET
                licence_number = ?, contact_name = ?, contact_phone = ?, test_type_id = ?, 
                region_id = ?, centre_id = ?, available_time = ?, email = ?, card_number = ?, 
                expiry_month = ?,expiry_year = ?, data = ?, cvn = ?
            WHERE id = ?
        ''', [
            data['licence_number'],
            data['contact_name'],
            data['contact_phone'],
            data['test_type_id'],
            data['region_id'],
            data['centre_id'],
            data['available_time'],
            data['email'],
            data['card_number'],
            data['expiry_month'],  # 替换原expiry_date
            data['expiry_year'],  # 新增年份
            data['data'],
            data['cvn'],
            id
        ])
        flash('记录更新成功', 'success')
    except Exception as e:
        flash(f'更新失败: {str(e)}', 'danger')
    return redirect(url_for('index'))


@app.route('/delete-booking/<int:id>', methods=['POST'])
def delete_booking(id):
    execute_db('DELETE FROM bookings WHERE id = ?', [id])
    flash('记录已删除', 'success')
    return redirect(url_for('index'))


logging.basicConfig(filename='booking.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == '__main__':
    # 初始化数据库（如果不存在）
    if not os.path.exists(app.config['DATABASE']):
        init_db()
    app.run(debug=True)
