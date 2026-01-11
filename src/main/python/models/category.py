"""
维修类别模型
============
对应数据库的 repair_categories 表。
"""

from datetime import datetime
from ..app import db


class RepairCategory(db.Model):
    """
    维修类别模型

    属性说明：
    - id: 类别唯一标识
    - name: 类别名称，如"水管维修"
    - description: 类别描述
    - status: 状态（启用/禁用）
    """

    __tablename__ = 'repair_categories'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='类别名称')
    description = db.Column(db.String(200), comment='类别描述')
    status = db.Column(
        db.Enum('active', 'disabled'),
        nullable=False,
        default='active',
        comment='状态'
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 关系：一个类别可以有多个工单
    work_orders = db.relationship('WorkOrder', backref='category', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'status': self.status
        }

    def __repr__(self):
        return f'<RepairCategory {self.id}: {self.name}>'
