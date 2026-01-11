"""
评价模型
========
对应数据库的 evaluations 表。
存储居民对维修服务的评价。
"""

from datetime import datetime
from ..app import db


class Evaluation(db.Model):
    """
    评价模型

    属性说明：
    - id: 评价唯一标识
    - work_order_id: 工单ID（唯一，一个工单只能有一条评价）
    - user_id: 评价人ID（居民）
    - rating: 评分（1-5星）
    - content: 评价内容（选填）
    """

    __tablename__ = 'evaluations'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    work_order_id = db.Column(
        db.Integer,
        db.ForeignKey('work_orders.id', ondelete='CASCADE'),
        unique=True,  # 一个工单只能有一条评价
        nullable=False,
        comment='工单ID'
    )
    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id'),
        nullable=False,
        comment='评价人ID'
    )
    rating = db.Column(db.SmallInteger, nullable=False, comment='评分1-5')
    content = db.Column(db.String(500), comment='评价内容')
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)

    # 关系：评价人
    user = db.relationship('User', foreign_keys=[user_id])

    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'rating': self.rating,
            'content': self.content,
            'user': self.user.to_dict() if self.user else None,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def __repr__(self):
        return f'<Evaluation {self.id}: {self.rating}星>'
