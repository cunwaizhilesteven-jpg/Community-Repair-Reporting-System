"""
工单接口
========
居民和维修人员使用的工单相关接口。

居民可以：提交工单、查看自己的工单、评价工单
维修人员可以：查看分配给自己的工单、开始处理、完成工单
"""

from datetime import datetime
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app import db
from models import (
    User, WorkOrder, WorkOrderImage, WorkOrderLog,
    Evaluation, RepairCategory, Building
)

# 创建蓝图
work_order_bp = Blueprint('work_order', __name__)


# ============================================
# 居民端接口
# ============================================

@work_order_bp.route('/work-orders', methods=['POST'])
@jwt_required()
def create_work_order():
    """
    居民提交报修工单

    请求参数（JSON）：
    - category_id: 维修类别ID（必填）
    - description: 问题描述（必填）
    - contact_phone: 联系电话（必填）
    - building_id: 楼栋ID（选填）
    - unit: 单元号（选填）
    - room: 房号（选填）
    - location_desc: 位置描述（选填，公共区域时使用）
    - images: 图片URL列表（选填）
    """

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()

    # 验证必填字段
    required_fields = ['category_id', 'description', 'contact_phone']
    for field in required_fields:
        if not data.get(field):
            return jsonify({'code': 400, 'message': f'缺少必填字段: {field}'}), 400

    # 验证维修类别是否存在
    category = RepairCategory.query.get(data['category_id'])
    if not category or category.status != 'active':
        return jsonify({'code': 400, 'message': '维修类别不存在或已禁用'}), 400

    # 验证楼栋（如果提供）
    building_id = data.get('building_id')
    if building_id:
        building = Building.query.get(building_id)
        if not building:
            return jsonify({'code': 400, 'message': '楼栋不存在'}), 400

    # 创建工单
    work_order = WorkOrder(
        order_no=WorkOrder.generate_order_no(),
        user_id=user_id,
        category_id=data['category_id'],
        building_id=building_id,
        unit=data.get('unit'),
        room=data.get('room'),
        location_desc=data.get('location_desc'),
        description=data['description'],
        contact_phone=data['contact_phone'],
        status=WorkOrder.STATUS_PENDING
    )
    db.session.add(work_order)
    db.session.flush()  # 获取工单ID，但还没提交事务

    # 保存报修图片
    images = data.get('images', [])
    for image_url in images:
        image = WorkOrderImage(
            work_order_id=work_order.id,
            image_url=image_url,
            type=WorkOrderImage.TYPE_REPORT
        )
        db.session.add(image)

    # 记录日志
    log = WorkOrderLog(
        work_order_id=work_order.id,
        operator_id=user_id,
        action=WorkOrderLog.ACTION_CREATE,
        from_status=None,
        to_status=WorkOrder.STATUS_PENDING,
        remark='居民提交报修'
    )
    db.session.add(log)

    # 提交事务
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '报修提交成功',
        'data': work_order.to_dict()
    })


@work_order_bp.route('/work-orders/mine', methods=['GET'])
@jwt_required()
def get_my_work_orders():
    """
    获取我的工单列表（居民）

    查询参数：
    - status: 按状态筛选（选填）
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    """

    user_id = int(get_jwt_identity())

    # 获取查询参数
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 构建查询
    query = WorkOrder.query.filter_by(user_id=user_id)

    if status:
        query = query.filter_by(status=status)

    # 按创建时间倒序（最新的在前面）
    query = query.order_by(WorkOrder.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [order.to_dict() for order in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@work_order_bp.route('/work-orders/<int:order_id>', methods=['GET'])
@jwt_required()
def get_work_order(order_id):
    """
    获取工单详情

    参数：
    - order_id: 工单ID（URL路径参数）
    """

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 权限检查：只能查看自己的工单，或者管理员/维修人员可以查看分配给自己的
    if work_order.user_id != user_id:
        if not (user.is_admin() or work_order.assigned_to == user_id):
            return jsonify({'code': 403, 'message': '没有权限查看此工单'}), 403

    return jsonify({
        'code': 200,
        'data': work_order.to_dict(include_details=True)
    })


@work_order_bp.route('/work-orders/<int:order_id>/logs', methods=['GET'])
@jwt_required()
def get_work_order_logs(order_id):
    """
    获取工单进度时间线

    返回工单的所有状态变更记录。
    """

    user_id = int(get_jwt_identity())

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 权限检查
    if work_order.user_id != user_id:
        user = User.query.get(user_id)
        if not (user.is_admin() or work_order.assigned_to == user_id):
            return jsonify({'code': 403, 'message': '没有权限查看此工单'}), 403

    logs = work_order.logs.order_by(WorkOrderLog.created_at).all()

    return jsonify({
        'code': 200,
        'data': [log.to_dict() for log in logs]
    })


@work_order_bp.route('/work-orders/<int:order_id>/evaluate', methods=['POST'])
@jwt_required()
def evaluate_work_order(order_id):
    """
    居民评价工单

    请求参数（JSON）：
    - rating: 评分1-5（必填）
    - content: 评价内容（选填）
    """

    user_id = int(get_jwt_identity())

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 只能评价自己的工单
    if work_order.user_id != user_id:
        return jsonify({'code': 403, 'message': '只能评价自己的工单'}), 403

    # 只能评价已完成的工单
    if work_order.status != WorkOrder.STATUS_COMPLETED:
        return jsonify({'code': 400, 'message': '只能评价已完成的工单'}), 400

    # 检查是否已评价
    if work_order.evaluation:
        return jsonify({'code': 400, 'message': '此工单已评价'}), 400

    data = request.get_json()

    # 验证评分
    rating = data.get('rating')
    if not rating or not (1 <= rating <= 5):
        return jsonify({'code': 400, 'message': '评分必须在1-5之间'}), 400

    # 创建评价
    evaluation = Evaluation(
        work_order_id=order_id,
        user_id=user_id,
        rating=rating,
        content=data.get('content')
    )
    db.session.add(evaluation)

    # 更新工单状态
    old_status = work_order.status
    work_order.status = WorkOrder.STATUS_EVALUATED

    # 记录日志
    log = WorkOrderLog(
        work_order_id=order_id,
        operator_id=user_id,
        action=WorkOrderLog.ACTION_EVALUATE,
        from_status=old_status,
        to_status=WorkOrder.STATUS_EVALUATED,
        remark=f'居民评价：{rating}星'
    )
    db.session.add(log)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '评价成功',
        'data': evaluation.to_dict()
    })


# ============================================
# 维修人员端接口
# ============================================

@work_order_bp.route('/repairman/work-orders', methods=['GET'])
@jwt_required()
def get_repairman_work_orders():
    """
    维修人员获取自己的工单列表

    查询参数：
    - status: 按状态筛选（选填）
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    """

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    # 验证是否是维修人员
    if not user.is_repairman() and not user.is_admin():
        return jsonify({'code': 403, 'message': '只有维修人员可以访问此接口'}), 403

    # 获取查询参数
    status = request.args.get('status')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 构建查询：只查询分配给自己的工单
    query = WorkOrder.query.filter_by(assigned_to=user_id)

    if status:
        query = query.filter_by(status=status)

    query = query.order_by(WorkOrder.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [order.to_dict() for order in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@work_order_bp.route('/repairman/work-orders/<int:order_id>/start', methods=['PUT'])
@jwt_required()
def start_work_order(order_id):
    """
    维修人员开始处理工单
    """

    user_id = int(get_jwt_identity())
    user = User.query.get(user_id)

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 验证是否是分配给自己的工单
    if work_order.assigned_to != user_id:
        return jsonify({'code': 403, 'message': '此工单不是分配给您的'}), 403

    # 验证工单状态
    if work_order.status != WorkOrder.STATUS_ASSIGNED:
        return jsonify({'code': 400, 'message': '只能开始处理已分配的工单'}), 400

    # 更新状态
    old_status = work_order.status
    work_order.status = WorkOrder.STATUS_PROCESSING

    # 记录日志
    log = WorkOrderLog(
        work_order_id=order_id,
        operator_id=user_id,
        action=WorkOrderLog.ACTION_START,
        from_status=old_status,
        to_status=WorkOrder.STATUS_PROCESSING,
        remark='维修人员开始处理'
    )
    db.session.add(log)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '已开始处理',
        'data': work_order.to_dict()
    })


@work_order_bp.route('/repairman/work-orders/<int:order_id>/complete', methods=['PUT'])
@jwt_required()
def complete_work_order(order_id):
    """
    维修人员完成工单

    请求参数（JSON）：
    - remark: 维修说明（选填）
    - images: 维修完成图片URL列表（选填）
    """

    user_id = int(get_jwt_identity())

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 验证是否是分配给自己的工单
    if work_order.assigned_to != user_id:
        return jsonify({'code': 403, 'message': '此工单不是分配给您的'}), 403

    # 验证工单状态
    if work_order.status != WorkOrder.STATUS_PROCESSING:
        return jsonify({'code': 400, 'message': '只能完成处理中的工单'}), 400

    data = request.get_json() or {}

    # 保存维修图片
    images = data.get('images', [])
    for image_url in images:
        image = WorkOrderImage(
            work_order_id=order_id,
            image_url=image_url,
            type=WorkOrderImage.TYPE_REPAIR
        )
        db.session.add(image)

    # 更新状态
    old_status = work_order.status
    work_order.status = WorkOrder.STATUS_COMPLETED
    work_order.completed_at = datetime.now()

    # 记录日志
    log = WorkOrderLog(
        work_order_id=order_id,
        operator_id=user_id,
        action=WorkOrderLog.ACTION_COMPLETE,
        from_status=old_status,
        to_status=WorkOrder.STATUS_COMPLETED,
        remark=data.get('remark', '维修完成')
    )
    db.session.add(log)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '工单已完成',
        'data': work_order.to_dict()
    })


@work_order_bp.route('/repairman/work-orders/<int:order_id>/images', methods=['POST'])
@jwt_required()
def add_repair_images(order_id):
    """
    维修人员上传维修过程图片

    请求参数（JSON）：
    - images: 图片URL列表
    """

    user_id = int(get_jwt_identity())

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 验证是否是分配给自己的工单
    if work_order.assigned_to != user_id:
        return jsonify({'code': 403, 'message': '此工单不是分配给您的'}), 403

    data = request.get_json()
    images = data.get('images', [])

    if not images:
        return jsonify({'code': 400, 'message': '请提供图片URL'}), 400

    # 保存图片
    for image_url in images:
        image = WorkOrderImage(
            work_order_id=order_id,
            image_url=image_url,
            type=WorkOrderImage.TYPE_REPAIR
        )
        db.session.add(image)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '图片上传成功'
    })
