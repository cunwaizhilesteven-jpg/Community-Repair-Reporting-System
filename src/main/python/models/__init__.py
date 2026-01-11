"""
数据模型模块
============
导出所有数据模型，方便其他地方导入使用。

使用方式：
    from models import User, WorkOrder, Building
"""

from .user import User
from .building import Building
from .category import RepairCategory
from .work_order import WorkOrder
from .work_order_image import WorkOrderImage
from .work_order_log import WorkOrderLog
from .evaluation import Evaluation

# 导出所有模型
__all__ = [
    'User',
    'Building',
    'RepairCategory',
    'WorkOrder',
    'WorkOrderImage',
    'WorkOrderLog',
    'Evaluation'
]
