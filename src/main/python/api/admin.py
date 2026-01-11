"""
物业管理员接口
==============
物业管理员使用的接口：工单管理、类别管理、统计报表等。
"""

from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from ..app import db
from ..models import (
    User, WorkOrder, WorkOrderLog, RepairCategory,
    Evaluation
)

# 创建蓝图
admin_bp = Blueprint('admin', __name__)


def admin_required(fn):
    """
    装饰器：要求管理员权限

    为什么需要这个装饰器？
    - 管理员接口需要验证用户是否有管理员权限
    - 把权限检查逻辑提取出来，避免每个接口都写一遍
    """
    from functools import wraps

    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user_id = get_jwt_identity()
        user = User.query.get(user_id)

        if not user or not user.is_admin():
            return jsonify({'code': 403, 'message': '需要管理员权限'}), 403

        return fn(*args, **kwargs)

    return wrapper


# ============================================
# 工单管理接口
# ============================================

@admin_bp.route('/work-orders', methods=['GET'])
@admin_required
def get_all_work_orders():
    """
    获取所有工单列表（支持筛选）

    查询参数：
    - status: 按状态筛选
    - category_id: 按类别筛选
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）
    - keyword: 关键词搜索（工单编号、描述）
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    """

    # 获取查询参数
    status = request.args.get('status')
    category_id = request.args.get('category_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    keyword = request.args.get('keyword')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # 构建查询
    query = WorkOrder.query

    if status:
        query = query.filter_by(status=status)

    if category_id:
        query = query.filter_by(category_id=category_id)

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

    if keyword:
        query = query.filter(
            db.or_(
                WorkOrder.order_no.like(f'%{keyword}%'),
                WorkOrder.description.like(f'%{keyword}%')
            )
        )

    # 按创建时间倒序
    query = query.order_by(WorkOrder.created_at.desc())

    # 分页
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'code': 200,
        'data': {
            'items': [order.to_dict(include_details=True) for order in pagination.items],
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })


@admin_bp.route('/work-orders/<int:order_id>/assign', methods=['PUT'])
@admin_required
def assign_work_order(order_id):
    """
    分配工单给维修人员

    请求参数（JSON）：
    - repairman_id: 维修人员ID（必填）
    """

    user_id = get_jwt_identity()

    work_order = WorkOrder.query.get(order_id)

    if not work_order:
        return jsonify({'code': 404, 'message': '工单不存在'}), 404

    # 只能分配待审核的工单
    if work_order.status != WorkOrder.STATUS_PENDING:
        return jsonify({'code': 400, 'message': '只能分配待审核的工单'}), 400

    data = request.get_json()
    repairman_id = data.get('repairman_id')

    if not repairman_id:
        return jsonify({'code': 400, 'message': '请选择维修人员'}), 400

    # 验证维修人员是否存在且是维修人员角色
    repairman = User.query.get(repairman_id)
    if not repairman or repairman.role != 'repairman':
        return jsonify({'code': 400, 'message': '维修人员不存在'}), 400

    if repairman.status != 'active':
        return jsonify({'code': 400, 'message': '维修人员已被禁用'}), 400

    # 更新工单
    old_status = work_order.status
    work_order.status = WorkOrder.STATUS_ASSIGNED
    work_order.assigned_to = repairman_id
    work_order.assigned_at = datetime.now()

    # 记录日志
    log = WorkOrderLog(
        work_order_id=order_id,
        operator_id=user_id,
        action=WorkOrderLog.ACTION_ASSIGN,
        from_status=old_status,
        to_status=WorkOrder.STATUS_ASSIGNED,
        remark=f'分配给维修人员: {repairman.name}'
    )
    db.session.add(log)

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '分配成功',
        'data': work_order.to_dict(include_details=True)
    })


@admin_bp.route('/repairmen', methods=['GET'])
@admin_required
def get_repairmen():
    """
    获取维修人员列表

    用于分配工单时选择维修人员。
    """

    repairmen = User.query.filter_by(role='repairman', status='active').all()

    return jsonify({
        'code': 200,
        'data': [r.to_dict() for r in repairmen]
    })


# ============================================
# 维修类别管理接口
# ============================================

@admin_bp.route('/categories', methods=['POST'])
@admin_required
def create_category():
    """
    添加维修类别

    请求参数（JSON）：
    - name: 类别名称（必填）
    - description: 类别描述（选填）
    """

    data = request.get_json()

    name = data.get('name')
    if not name:
        return jsonify({'code': 400, 'message': '类别名称不能为空'}), 400

    # 检查名称是否重复
    existing = RepairCategory.query.filter_by(name=name).first()
    if existing:
        return jsonify({'code': 400, 'message': '类别名称已存在'}), 400

    category = RepairCategory(
        name=name,
        description=data.get('description'),
        status='active'
    )
    db.session.add(category)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '添加成功',
        'data': category.to_dict()
    })


@admin_bp.route('/categories/<int:category_id>', methods=['PUT'])
@admin_required
def update_category(category_id):
    """
    编辑维修类别

    请求参数（JSON）：
    - name: 类别名称（选填）
    - description: 类别描述（选填）
    - status: 状态 active/disabled（选填）
    """

    category = RepairCategory.query.get(category_id)

    if not category:
        return jsonify({'code': 404, 'message': '类别不存在'}), 404

    data = request.get_json()

    if 'name' in data:
        # 检查名称是否重复
        existing = RepairCategory.query.filter(
            RepairCategory.name == data['name'],
            RepairCategory.id != category_id
        ).first()
        if existing:
            return jsonify({'code': 400, 'message': '类别名称已存在'}), 400
        category.name = data['name']

    if 'description' in data:
        category.description = data['description']

    if 'status' in data:
        category.status = data['status']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': category.to_dict()
    })


@admin_bp.route('/categories/<int:category_id>', methods=['DELETE'])
@admin_required
def delete_category(category_id):
    """
    删除维修类别

    注意：如果有工单使用了此类别，不能删除。
    """

    category = RepairCategory.query.get(category_id)

    if not category:
        return jsonify({'code': 404, 'message': '类别不存在'}), 404

    # 检查是否有工单使用此类别
    if category.work_orders.count() > 0:
        return jsonify({'code': 400, 'message': '此类别下有工单，不能删除'}), 400

    db.session.delete(category)
    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '删除成功'
    })


# ============================================
# 统计报表接口
# ============================================

@admin_bp.route('/statistics', methods=['GET'])
@admin_required
def get_statistics():
    """
    获取统计数据

    查询参数：
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）

    返回：
    - total: 工单总数
    - by_status: 按状态分布
    - by_category: 按类别分布
    - avg_process_time: 平均处理时长（小时）
    - rating_stats: 评价统计
    """

    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # 基础查询
    query = WorkOrder.query

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

    # 总数
    total = query.count()

    # 按状态分布
    status_stats = db.session.query(
        WorkOrder.status,
        func.count(WorkOrder.id)
    ).group_by(WorkOrder.status).all()

    by_status = {status: count for status, count in status_stats}

    # 按类别分布
    category_stats = db.session.query(
        RepairCategory.name,
        func.count(WorkOrder.id)
    ).join(WorkOrder).group_by(RepairCategory.id).all()

    by_category = {name: count for name, count in category_stats}

    # 平均处理时长（已完成的工单）
    completed_orders = query.filter(
        WorkOrder.status.in_([WorkOrder.STATUS_COMPLETED, WorkOrder.STATUS_EVALUATED]),
        WorkOrder.completed_at.isnot(None)
    ).all()

    if completed_orders:
        total_hours = sum(
            (order.completed_at - order.created_at).total_seconds() / 3600
            for order in completed_orders
        )
        avg_process_time = round(total_hours / len(completed_orders), 2)
    else:
        avg_process_time = 0

    # 评价统计
    rating_stats = db.session.query(
        Evaluation.rating,
        func.count(Evaluation.id)
    ).group_by(Evaluation.rating).all()

    rating_distribution = {rating: count for rating, count in rating_stats}

    avg_rating = db.session.query(func.avg(Evaluation.rating)).scalar()
    avg_rating = round(float(avg_rating), 2) if avg_rating else 0

    return jsonify({
        'code': 200,
        'data': {
            'total': total,
            'by_status': by_status,
            'by_category': by_category,
            'avg_process_time': avg_process_time,
            'rating_stats': {
                'distribution': rating_distribution,
                'average': avg_rating
            }
        }
    })


@admin_bp.route('/evaluations', methods=['GET'])
@admin_required
def get_evaluations():
    """
    获取评价列表

    查询参数：
    - rating: 按评分筛选
    - page: 页码，默认1
    - per_page: 每页数量，默认10
    """

    rating = request.args.get('rating', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Evaluation.query

    if rating:
        query = query.filter_by(rating=rating)

    query = query.order_by(Evaluation.created_at.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    # 构建返回数据，包含关联的工单信息
    items = []
    for evaluation in pagination.items:
        item = evaluation.to_dict()
        item['work_order'] = {
            'id': evaluation.work_order.id,
            'order_no': evaluation.work_order.order_no
        } if evaluation.work_order else None
        items.append(item)

    return jsonify({
        'code': 200,
        'data': {
            'items': items,
            'total': pagination.total,
            'page': page,
            'per_page': per_page,
            'pages': pagination.pages
        }
    })
