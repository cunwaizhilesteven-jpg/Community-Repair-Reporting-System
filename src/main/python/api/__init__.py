"""
API 接口模块
============
导出所有蓝图，方便在 app.py 中注册。
"""

from .auth import auth_bp
from .common import common_bp
from .work_order import work_order_bp
from .admin import admin_bp
from .super_admin import super_bp

__all__ = [
    'auth_bp',
    'common_bp',
    'work_order_bp',
    'admin_bp',
    'super_bp'
]
