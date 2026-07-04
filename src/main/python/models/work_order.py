"""
工单模型
========
对应数据库的 work_orders 表。
这是系统最核心的模型，存储所有报修工单。
"""

from datetime import datetime
from app import db


class WorkOrder(db.Model):
    """
    工单模型

    属性说明：
    - id: 工单唯一标识
    - order_no: 工单编号，如"WO202601110001"
    - user_id: 报修居民ID
    - category_id: 维修类别ID
    - building_id: 楼栋ID（可为空）
    - unit: 单元号
    - room: 房号
    - location_desc: 位置描述
    - description: 问题描述
    - contact_phone: 联系电话
    - status: 工单状态
    - assigned_to: 被分配的维修人员ID
    """

    __tablename__ = 'work_orders'

    # 工单状态常量
    STATUS_PENDING = 'pending'       # 待审核
    STATUS_ASSIGNED = 'assigned'     # 已分配
    STATUS_PROCESSING = 'processing' # 处理中
    STATUS_COMPLETED = 'completed'   # 已完成
    STATUS_EVALUATED = 'evaluated'   # 已评价

    # 状态中文映射
    STATUS_NAMES = {
        'pending': '待审核',
        'assigned': '已分配',
        'processing': '处理中',
        'completed': '已完成',
        'evaluated': '已评价'
    }

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_no = db.Column(db.String(20), unique=True, nullable=False, comment='工单编号')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, comment='报修居民ID')
    category_id = db.Column(db.Integer, db.ForeignKey('repair_categories.id'), nullable=False, comment='维修类别ID')
    building_id = db.Column(db.Integer, db.ForeignKey('buildings.id'), comment='楼栋ID')
    unit = db.Column(db.String(10), comment='单元号')
    room = db.Column(db.String(10), comment='房号')
    location_desc = db.Column(db.String(200), comment='位置描述')
    description = db.Column(db.Text, nullable=False, comment='问题描述')
    contact_phone = db.Column(db.String(20), nullable=False, comment='联系电话')
    status = db.Column(
        db.Enum('pending', 'assigned', 'processing', 'completed', 'evaluated'),
        nullable=False,
        default='pending',
        comment='工单状态'
    )
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'), comment='维修人员ID')
    assigned_at = db.Column(db.DateTime, comment='分配时间')
    completed_at = db.Column(db.DateTime, comment='完成时间')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.now, onupdate=datetime.now)

    # 关系定义
    # 维修人员（通过 assigned_to 字段关联）
    repairman = db.relationship(
        'User',
        foreign_keys=[assigned_to],
        backref='assigned_orders'
    )

    # 工单图片
    images = db.relationship('WorkOrderImage', backref='work_order', lazy='dynamic', cascade='all, delete-orphan')

    # 工单日志
    logs = db.relationship('WorkOrderLog', backref='work_order', lazy='dynamic', cascade='all, delete-orphan')

    # 评价（一对一）
    evaluation = db.relationship('Evaluation', backref='work_order', uselist=False, cascade='all, delete-orphan')

    @staticmethod
    def generate_order_no():
        """
        生成工单编号

        格式：WO + 年月日 + 4位序号
        例如：WO202601110001

        为什么这样设计？
        - WO 前缀表示这是工单(Work Order)
        - 日期方便按时间查找
        - 4位序号支持每天9999个工单
        """
        today = datetime.now().strftime('%Y%m%d')
        prefix = f'WO{today}'

        # 查询今天最大的工单号
        last_order = WorkOrder.query.filter(
            WorkOrder.order_no.like(f'{prefix}%')
        ).order_by(WorkOrder.order_no.desc()).first()

        if last_order:
            # 取出最后4位数字，加1
            last_num = int(last_order.order_no[-4:])
            new_num = last_num + 1
        else:
            # 今天第一个工单
            new_num = 1

        return f'{prefix}{new_num:04d}'

    def to_dict(self, include_details=False):
        """
        转换为字典

        参数：
            include_details: 是否包含详细信息（图片、日志等）
        """
        result = {
            'id': self.id,
            'order_no': self.order_no,
            'category': self.category.to_dict() if self.category else None,
            'building': self.building.to_dict() if self.building else None,
            'unit': self.unit,
            'room': self.room,
            'location_desc': self.location_desc,
            'description': self.description,
            'contact_phone': self.contact_phone,
            'status': self.status,
            'status_name': self.STATUS_NAMES.get(self.status, self.status),
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None,
            'assigned_at': self.assigned_at.strftime('%Y-%m-%d %H:%M:%S') if self.assigned_at else None,
            'completed_at': self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else None
        }

        if include_details:
            # 包含报修人信息
            result['user'] = self.user.to_dict() if self.user else None
            # 包含维修人员信息
            result['repairman'] = self.repairman.to_dict() if self.repairman else None
            # 包含图片列表
            result['images'] = [img.to_dict() for img in self.images]
            # 包含日志列表
            result['logs'] = [log.to_dict() for log in self.logs.order_by(db.text('created_at'))]
            # 包含评价
            result['evaluation'] = self.evaluation.to_dict() if self.evaluation else None

        return result

    def __repr__(self):
        return f'<WorkOrder {self.order_no}>'
