"""
用户模型
========
对应数据库的 users 表。

这个类定义了用户的数据结构和相关操作。
"""

from datetime import datetime
from app import db


class User(db.Model):
    """
    用户模型

    属性说明：
    - id: 用户唯一标识
    - openid: 微信小程序的用户标识
    - phone: 手机号
    - name: 姓名
    - role: 角色（居民/维修人员/管理员/超管）
    - status: 状态（正常/禁用）
    """

    # 指定对应的数据库表名
    __tablename__ = 'users'

    # 定义字段（列）
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    openid = db.Column(db.String(64), unique=True, comment='微信openid')
    phone = db.Column(db.String(20), comment='手机号')
    name = db.Column(db.String(50), nullable=False, comment='姓名')
    role = db.Column(
        db.Enum('resident', 'repairman', 'admin', 'super'),
        nullable=False,
        default='resident',
        comment='角色'
    )
    status = db.Column(
        db.Enum('active', 'disabled'),
        nullable=False,
        default='active',
        comment='状态'
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.now)
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.now,
        onupdate=datetime.now
    )

    # 定义关系（一个用户可以有多个工单）
    # backref='user' 表示可以从工单反向访问用户：work_order.user
    work_orders = db.relationship(
        'WorkOrder',
        backref='user',
        lazy='dynamic',
        foreign_keys='WorkOrder.user_id'
    )

    def to_dict(self):
        """
        将用户对象转换为字典

        为什么需要这个方法？
        - API 返回的是 JSON 格式
        - JSON 不能直接包含 Python 对象
        - 需要先转成字典，再转成 JSON
        """
        return {
            'id': self.id,
            'phone': self.phone,
            'name': self.name,
            'role': self.role,
            'status': self.status,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else None
        }

    def is_admin(self):
        """判断是否是管理员（包括超管）"""
        return self.role in ['admin', 'super']

    def is_super(self):
        """判断是否是超级管理员"""
        return self.role == 'super'

    def is_repairman(self):
        """判断是否是维修人员"""
        return self.role == 'repairman'

    def __repr__(self):
        """打印对象时显示的内容，方便调试"""
        return f'<User {self.id}: {self.name}>'
