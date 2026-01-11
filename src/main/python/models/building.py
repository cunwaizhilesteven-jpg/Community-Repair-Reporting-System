"""
楼栋模型
========
对应数据库的 buildings 表。
"""

from datetime import datetime
from ..app import db


class Building(db.Model):
    """
    楼栋模型

    属性说明：
    - id: 楼栋唯一标识
    - name: 楼栋名称，如"1栋"、"A座"
    - units: 单元数量
    - floors: 楼层数
    """

    __tablename__ = 'buildings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(50), nullable=False, comment='楼栋名称')
    units = db.Column(db.Integer, nullable=False, default=1, comment='单元数量')
    floors = db.Column(db.Integer, nullable=False, default=1, comment='楼层数')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 关系：一个楼栋可以有多个工单
    work_orders = db.relationship('WorkOrder', backref='building', lazy='dynamic')

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'name': self.name,
            'units': self.units,
            'floors': self.floors
        }

    def __repr__(self):
        return f'<Building {self.id}: {self.name}>'
