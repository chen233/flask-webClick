from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# 配置SQLite数据库（数据库文件将生成在项目根目录）
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///learner_licence.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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

    def to_dict(self):
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
            'email': self.email
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