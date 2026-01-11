"""
工单图片模型
============
对应数据库的 work_order_images 表。
存储报修时和维修完成后上传的图片。
"""

from datetime import datetime
from ..app import db


class WorkOrderImage(db.Model):
    """
    工单图片模型

    属性说明：
    - id: 图片唯一标识
    - work_order_id: 所属工单ID
    - image_url: 图片URL地址
    - type: 图片类型（report=报修图片, repair=维修图片）
    """

    __tablename__ = 'work_order_images'

    # 图片类型常量
    TYPE_REPORT = 'report'  # 报修时上传的图片
    TYPE_REPAIR = 'repair'  # 维修完成后上传的图片

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey('work_orders.id', ondelete='CASCADE'),
        nullable=False,
        comment='工单ID'
    )
    image_url = db.Column(db.String(255), nullable=False, comment='图片URL')
    type = db.Column(
        db.Enum('report', 'repair'),
        nullable=False,
        default='report',
        comment='图片类型'
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'image_url': self.image_url,
            'type': self.type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<WorkOrderImage {self.id}>'
