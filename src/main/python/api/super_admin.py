"""
超级管理员接口
==============
超级管理员使用的接口：用户管理、楼栋管理、数据导出等。
"""

from datetime import datetime, timedelta
from io import BytesIO
from flask import Blueprint, request, jsonify, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity
from openpyxl import Workbook
from ..app import db
from ..models import User, Building, WorkOrder

# 创建蓝图
super_bp = Blueprint('super', __name__)


def super_required(fn):
    """
    装饰器：要求超级管理员权限
    """
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_super():
            return jsonify({'code': 403, 'message': '需要超级管理员权限'}), 403

        return fn(*args, **kwargs)

    return wrapper


# ============================================
# 用户管理接口
# ============================================

@super_bp.route('/users', methods=['GET'])
@super_required
def get_users():
    """
    获取用户列表

    查询参数：
    - role: 按角色筛选
    - status: 按状态筛选
    - keyword: 关键词搜索（姓名、手机号）
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    """

    role = request.args.get('role')
    status = request.args.get('status')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = User.query

    if role:
        query = query.filter_by(role=role)

    if status:
        query = query.filter_by(status=status)

    if keyword:
        query = query.filter(
            db.or_(
                User.name.like(f'%{keyword}%'),
                User.phone.like(f'%{keyword}%')
            )
        )

    query = query.order_by(User.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [u.to_dict() for u in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@super_bp.route('/users', methods=['POST'])
@super_required
def create_user():
    """
    创建用户

    请求参数（JSON）：
    - name: 姓名（必填）
    - phone: 手机号（必填）
    - role: 角色（必填）resident/repairman/admin
    """

    data = request.get_json()

    # 验证必填字段
    required_fields = ['name', 'phone', 'role']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'code': 400, 'message': f'缺少必填字段: {field}'}), 400

    # 验证角色
    valid_roles = ['resident', 'repairman', 'admin']
    if data['role'] not in valid_roles:
        return jsonify({'code': 400, 'message': '无效的角色'}), 400

    # 检查手机号是否已存在
    existing = User.query.filter_by(phone=data['phone']).first()
    if existing:
        return jsonify({'code': 400, 'message': '手机号已存在'}), 400

    user = User(
        name=data['name'],
        phone=data['phone'],
        role=data['role'],
        status='active'
    )
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '创建成功',
        'data': user.to_dict()
    })


@super_bp.route('/users/<int:user_id>', methods=['PUT'])
@super_required
def update_user(user_id):
    """
    编辑用户

    请求参数（JSON）：
    - name: 姓名（选填）
    - phone: 手机号（选填）
    - role: 角色（选填）
    """

    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    # 不能修改超级管理员
    if user.is_super():
        return jsonify({'code': 403, 'message': '不能修改超级管理员'}), 403

    data = request.get_json()

    if 'name' in data:
        user.name = data['name']

    if 'phone' in data:
        # 检查手机号是否已被其他用户使用
        existing = User.query.filter(
            User.phone == data['phone'],
            User.id != user_id
        ).first()
        if existing:
            return jsonify({'code': 400, 'message': '手机号已存在'}), 400
        user.phone = data['phone']

    if 'role' in data:
        valid_roles = ['resident', 'repairman', 'admin']
        if data['role'] not in valid_roles:
            return jsonify({'code': 400, 'message': '无效的角色'}), 400
        user.role = data['role']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


@super_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@super_required
def update_user_status(user_id):
    """
    启用/禁用用户

    请求参数（JSON）：
    - status: active/disabled（必填）
    """

    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    # 不能禁用超级管理员
    if user.is_super():
        return jsonify({'code': 403, 'message': '不能禁用超级管理员'}), 403

    data = request.get_json()
    status = data.get('status')

    if status not in ['active', 'disabled']:
        return jsonify({'code': 400, 'message': '无效的状态'}), 400

    user.status = status
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


# ============================================
# 楼栋管理接口
# ============================================

@super_bp.route('/buildings', methods=['POST'])
@super_required
def create_building():
    """
    添加楼栋

    请求参数（JSON）：
    - name: 楼栋名称（必填）
    - units: 单元数量（选填，默认1）
    - floors: 楼层数（选填，默认1）
    """

    data = request.get_json()

    name = data.get('name')
    if not name:
        return jsonify({'code': 400, 'message': '楼栋名称不能为空'}), 400

    # 检查名称是否重复
    existing = Building.query.filter_by(name=name).first()
    if existing:
        return jsonify({'code': 400, 'message': '楼栋名称已存在'}), 400

    building = Building(
        name=name,
        units=data.get('units', 1),
        floors=data.get('floors', 1)
    )
    db.session.add(building)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '添加成功',
        'data': building.to_dict()
    })


@super_bp.route('/buildings/<int:building_id>', methods=['PUT'])
@super_required
def update_building(building_id):
    """
    编辑楼栋
    """

    building = Building.query.get(building_id)

    if not building:
        return jsonify({'code': 404, 'message': '楼栋不存在'}), 404

    data = request.get_json()

    if 'name' in data:
        # 检查名称是否重复
        existing = Building.query.filter(
            Building.name == data['name'],
            Building.id != building_id
        ).first()
        if existing:
            return jsonify({'code': 400, 'message': '楼栋名称已存在'}), 400
        building.name = data['name']

    if 'units' in data:
        building.units = data['units']

    if 'floors' in data:
        building.floors = data['floors']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': building.to_dict()
    })


@super_bp.route('/buildings/<int:building_id>', methods=['DELETE'])
@super_required
def delete_building(building_id):
    """
    删除楼栋

    注意：如果有工单使用了此楼栋，不能删除。
    """

    building = Building.query.get(building_id)

    if not building:
        return jsonify({'code': 404, 'message': '楼栋不存在'}), 404

    # 检查是否有工单使用此楼栋
    if building.work_orders.count() > 0:
        return jsonify({'code': 400, 'message': '此楼栋下有工单，不能删除'}), 400

    db.session.delete(building)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ============================================
# 数据导出接口
# ============================================

@super_bp.route('/export/work-orders', methods=['GET'])
@super_required
def export_work_orders():
    """
    导出工单数据为 Excel

    查询参数：
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）
    - status: 按状态筛选
    """

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status = request.args.get('status')

    # 构建查询
    query = WorkOrder.query

    if status:
        query = query.filter_by(status=status)

    if start_date:
        try:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(WorkOrder.created_at >= start)
        except ValueError:
            pass

    if end_date:
        try:
            end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(WorkOrder.created_at < end)
        except ValueError:
            pass

    work_orders = query.order_by(WorkOrder.created_at.desc()).all()

    # 创建 Excel 工作簿
    wb = Workbook()
    ws = wb.active
    ws.title = '工单数据'

    # 写入表头
    headers = [
        '工单编号', '维修类别', '楼栋', '单元', '房号', '位置描述',
        '问题描述', '联系电话', '状态', '报修人', '维修人员',
        '报修时间', '分配时间', '完成时间', '评分'
    ]
    ws.append(headers)

    # 写入数据
    for order in work_orders:
        row = [
            order.order_no,
            order.category.name if order.category else '',
            order.building.name if order.building else '',
            order.unit or '',
            order.room or '',
            order.location_desc or '',
            order.description,
            order.contact_phone,
            WorkOrder.STATUS_NAMES.get(order.status, order.status),
            order.user.name if order.user else '',
            order.repairman.name if order.repairman else '',
            order.created_at.strftime('%Y-%m-%d %H:%M:%S') if order.created_at else '',
            order.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if order.assigned_at else '',
            order.completed_at.strftime('%Y-%m-%d %H:%M:%S') if order.completed_at else '',
            order.evaluation.rating if order.evaluation else ''
        ]
        ws.append(row)

    # 保存到内存中
    output = BytesIO()
    wb.save(output)
    output.seek(0)

    # 生成文件名
    filename = f'工单数据_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx'

    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )
