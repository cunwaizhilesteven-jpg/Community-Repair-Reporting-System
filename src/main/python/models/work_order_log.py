"""
工单日志模型
============
对应数据库的 work_order_logs 表。
记录工单的每一次状态变更，形成完整的进度时间线。
"""

from datetime import datetime
from app import db


class WorkOrderLog(db.Model):
    """
    工单日志模型

    属性说明：
    - id: 日志唯一标识
    - work_order_id: 所属工单ID
    - operator_id: 操作人ID
    - action: 操作类型
    - from_status: 变更前状态
    - to_status: 变更后状态
    - remark: 备注说明
    """

    __tablename__ = 'work_order_logs'

    # 操作类型常量
    ACTION_CREATE = 'create'      # 创建工单
    ACTION_AUDIT = 'audit'        # 审核
    ACTION_ASSIGN = 'assign'      # 分配
    ACTION_START = 'start'        # 开始处理
    ACTION_COMPLETE = 'complete'  # 完成
    ACTION_EVALUATE = 'evaluate'  # 评价

    # 操作类型中文映射
    ACTION_NAMES = {
        'create': '提交报修',
        'audit': '审核通过',
        'assign': '分配维修人员',
        'start': '开始处理',
        'complete': '维修完成',
        'evaluate': '居民评价'
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey('work_orders.id', ondelete='CASCADE'),
        nullable=False,
        comment='工单ID'
    )
    operator_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        comment='操作人ID'
    )
    action = db.Column(
        db.Enum('create', 'audit', 'assign', 'start', 'complete', 'evaluate'),
        nullable=False,
        comment='操作类型'
    )
    from_status = db.Column(db.String(20), comment='变更前状态')
    to_status = db.Column(db.String(20), comment='变更后状态')
    remark = db.Column(db.String(500), comment='备注说明')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 关系：操作人
    operator = db.relationship('User', foreign_keys=[operator_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'action': self.action,
            'action_name': self.ACTION_NAMES.get(self.action, self.action),
            'from_status': self.from_status,
            'to_status': self.to_status,
            'remark': self.remark,
            'operator': self.operator.to_dict() if self.operator else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<WorkOrderLog {self.id}: {self.action}>'
