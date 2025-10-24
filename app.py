from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
import time

app = Flask(__name__)

# 配置SQLite数据库（数据库文件将生成在项目根目录）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learner_licence.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
scheduler = BackgroundScheduler()


@app.route('/api/start_task', methods=['POST'])
def start_task():
    licence_number = request.args.get('licence_number')
    if not licence_number:
        return jsonify({"status": "error", "message": "请提供驾照号码"})

    record = LicenceRecord.query.get(licence_number)
    if not record:
        return jsonify({"status": "error", "message": "记录不存在"})

    # 强制设置状态为“运行中”
    record.status = 1
    db.session.commit()

    # 立即执行任务（也可以不立即执行，仅更新状态，由定时任务后续执行）
    try:
        task_result = execute_booking_task(record)
        record.status = 2  # 任务完成
        record.result = task_result
        db.session.commit()
        return jsonify({"status": "success", "message": "任务已执行完成"})
    except Exception as e:
        record.status = 0  # 执行失败，恢复未运行
        db.session.commit()
        return jsonify({"status": "error", "message": f"任务执行失败：{str(e)}"})
# 任务执行函数
def check_and_execute_tasks():
    with app.app_context():  # 激活Flask上下文
        records = LicenceRecord.query.all()
        now = datetime.now()

        for record in records:
            # 解析预约时间
            if not record.booking_time:
                continue

            try:
                # 格式示例："2025-10-03至2025-11-08 18:54-18:57"
                date_range, time_range = record.booking_time.split(' ')
                start_date_str, end_date_str = date_range.split('至')
                start_time_str, end_time_str = time_range.split('-')

                # 转换为datetime对象
                start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
                end_date = datetime.strptime(end_date_str, "%Y-%m-%d")
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                end_time = datetime.strptime(end_time_str, "%H:%M").time()

                # 检查日期范围
                if not (start_date <= now.date() <= end_date):
                    if now.date() > end_date:
                        record.status = 3  # 已过期
                        db.session.commit()
                    continue

                # 检查时间范围
                current_time = now.time()
                if start_time <= current_time <= end_time:
                    # 执行任务（这里替换为你的实际任务逻辑）
                    if record.status != 1:  # 避免重复执行
                        record.status = 1  # 运行中
                        db.session.commit()

                        # 模拟任务执行
                        task_result = execute_booking_task(record)

                        # 更新状态和结果
                        record.status = 2  # 已完成
                        record.result = task_result
                        db.session.commit()
                else:
                    if record.status == 1:
                        record.status = 0  # 未运行
                        db.session.commit()

            except Exception as e:
                print(f"处理任务出错: {str(e)}")
                continue


# 实际执行的任务函数（替换为你的业务逻辑）
def execute_booking_task(record):
    # 这里写你的循环函数逻辑
    time.sleep(2)  # 模拟耗时操作
    return f"任务完成于 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"


# 启动定时任务
def start_scheduler():
    scheduler.add_job(
        check_and_execute_tasks,
        'interval',  # 间隔执行
        seconds=30,  # 每30秒检查一次
        max_instances=1  # 避免并发问题
    )
    scheduler.start()


# 在应用启动时启动定时任务
with app.app_context():
    db.create_all()  # 确保表结构更新
start_scheduler()


# 新增API用于前端获取最新状态
@app.route('/api/status', methods=['GET'])
def get_status():
    records = LicenceRecord.query.all()
    return jsonify({
        "status": "success",
        "data": [record.to_dict() for record in records]
    })


# 定义数据模型
class LicenceRecord(db.Model):
    __tablename__ = 'licence_records'
    licence_number = db.Column(db.String(50), primary_key=True)  # 驾照号码作为主键
    contact_name = db.Column(db.String(100), nullable=False)
    contact_phone = db.Column(db.String(20), nullable=False)
    test_type = db.Column(db.String(100), nullable=False)
    region = db.Column(db.String(100), nullable=False)
    centre = db.Column(db.String(100), nullable=False)
    booking_time = db.Column(db.String(200))
    card_number = db.Column(db.String(50), nullable=False)
    expiry_month = db.Column(db.String(10), nullable=False)
    expiry_yy = db.Column(db.String(10), nullable=False)
    cvv = db.Column(db.String(10), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    status = db.Column(db.Integer, default=0)
    # 存储返回结果
    result = db.Column(db.Text, nullable=True)

    def to_dict(self):
        status_map = {0: "未运行", 1: "运行中", 2: "已完成", 3: "已过期"}
        return {
            'licence_number': self.licence_number,
            'contact_name': self.contact_name,
            'contact_phone': self.contact_phone,
            'test_type': self.test_type,
            'region': self.region,
            'centre': self.centre,
            'booking_time': self.booking_time,
            'card_number': self.card_number,
            'expiry_month': self.expiry_month,
            'expiry_yy': self.expiry_yy,
            'cvv': self.cvv,
            'email': self.email,
            'status': self.status,
            'status_text': status_map.get(self.status, "未知"),
            'result': self.result

        }
# 区域-考试中心映射
region_centre_map = {
    "SEQ BRISBANE NORTHSIDE（布里斯班北区）": ["Strathpine CSC", "Caboolture CSC", "Redcliffe CSC", "Zillmere CSC", "Toowong CSC"],
    "SEQ BRISBANE SOUTHSIDE（布里斯班南区）": ["Sherwood CSC", "Greenslopes CSC", "Cleveland CSC", "Ipswich CSC", "Wynnum CSC"],
    "SEQ LOGAN/BETHANIA（洛根/贝萨尼亚）": ["Bethania CSC", "Logan Driver Assessment C", "Logan City CSC"],
    "SEQ GOLD COAST（黄金海岸）": ["Southport CSC", "Burleigh Waters CSC", "Currumbin Waters CSC", "Helensvale CSC"],
    "SEQ SUNSHINE COAST & HINTERLAND（阳光海岸及内陆）": ["Caloundra CSC", "Tewantin CSC", "Nambour CSC", "Maroochydore CSC"]
}

# 考试类型选项
test_types = [
    {"value": "Class C/CA - Car (manual/automatic)", "label": "C/CA类 - 小型汽车（手动/自动）"},
    {"value": "Class LR - Light rigid vehicle", "label": "LR类 - 轻型刚性车辆"},
    {"value": "Class MR - Medium rigid vehicle", "label": "MR类 - 中型刚性车辆"},
    {"value": "Class HR - Heavy rigid vehicle", "label": "HR类 - 重型刚性车辆"},
    {"value": "Class HC - Heavy combination vehicle", "label": "HC类 - 重型组合车辆"}
]

@app.route('/')
def index():
    # 从数据库查询所有记录
    records = LicenceRecord.query.all()
    # 将对象列表转换为字典列表（关键修复）
    data = [record.to_dict() for record in records]
    return render_template(
        'index.html',
        data=data,  # 传递转换后的字典列表
        regions=list(region_centre_map.keys()),
        test_types=test_types,
        region_centre_map = region_centre_map  # 添加这一行

    )
@app.route('/api/region_centres', methods=['GET'])
def get_centres():
    region = request.args.get('region')
    return jsonify(region_centre_map.get(region, []))

@app.route('/api/data', methods=['GET'])
def get_data():
    licence_number = request.args.get('licence_number')
    record = LicenceRecord.query.get(licence_number)
    if record:
        # 将数据库对象转换为字典返回
        return jsonify({
            "status": "success",
            "data": {
                "licence_number": record.licence_number,
                "contact_name": record.contact_name,
                "contact_phone": record.contact_phone,
                "test_type": record.test_type,
                "region": record.region,
                "centre": record.centre,
                "booking_time": record.booking_time,
                "card_number": record.card_number,
                "expiry_month": record.expiry_month,
                "expiry_yy": record.expiry_yy,
                "cvv": record.cvv,
                "email": record.email
            }
        })
    return jsonify({"status": "error", "message": "Record not found"})


@app.route('/api/data', methods=['POST', 'PUT', 'DELETE'])
def handle_data():
    if request.method == 'POST':
        # 新增数据
        data = request.get_json()
        if not data.get('licence_number'):
            return jsonify({"status": "error", "message": "licence_number is required（驾照号码为必填项）"}), 400
        new_record = LicenceRecord(
            licence_number=data['licence_number'],
            contact_name=data['contact_name'],
            contact_phone=data['contact_phone'],
            test_type=data['test_type'],
            region=data['region'],
            centre=data['centre'],
            booking_time=data['booking_time'],
            card_number=data['card_number'],
            expiry_month=data['expiry_month'],
            expiry_yy=data['expiry_yy'],
            cvv=data['cvv'],
            email=data['email']
        )
        db.session.add(new_record)
        db.session.commit()
        return jsonify({"status": "success", "data": data})
    elif request.method == 'PUT':
        # 修改数据
        data = request.get_json()
        if not data.get('licence_number'):
            return jsonify({"status": "error", "message": "licence_number is required（驾照号码为必填项）"}), 400
        record = LicenceRecord.query.get(data['licence_number'])
        if record:
            record.contact_name = data['contact_name']
            record.contact_phone = data['contact_phone']
            record.test_type = data['test_type']
            record.region = data['region']
            record.centre = data['centre']
            record.booking_time = data['booking_time']
            record.card_number = data['card_number']
            record.expiry_month = data['expiry_month']
            record.expiry_yy = data['expiry_yy']
            record.cvv = data['cvv']
            record.email = data['email']
            db.session.commit()
            return jsonify({"status": "success", "data": data})
        return jsonify({"status": "error", "message": "Record not found"})
    elif request.method == 'DELETE':
        # 删除数据
        licence_number = request.args.get('licence_number')
        record = LicenceRecord.query.get(licence_number)
        if record:
            db.session.delete(record)
            db.session.commit()
            return jsonify({"status": "success", "licence_number": licence_number})
        return jsonify({"status": "error", "message": "Record not found"})

# 初始化数据库（首次运行时取消注释，创建表结构后再注释）
# with app.app_context():
#     db.create_all()

if __name__ == '__main__':
    app.run(debug=True)