"""
配置文件
========
存放项目的各种配置信息。

为什么要用配置文件？
- 把配置和代码分开，方便修改
- 不同环境（开发/生产）可以用不同配置
- 敏感信息（如数据库密码）不会写死在代码里
"""

import os
from datetime import timedelta

# 从环境变量读取配置，如果没有就用默认值
# 环境变量可以在 .env 文件中设置


class Config:
    """基础配置类"""

    # ============================================
    # Flask 基础配置
    # ============================================

    # 密钥：用于加密 session 和 token，生产环境一定要改！
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')

    # ============================================
    # 数据库配置
    # ============================================

    # 数据库连接地址
    # 格式：mysql+pymysql://用户名:密码@主机:端口/数据库名
    SQLALCHEMY_DATABASE_URI = os.getenv(
        'DATABASE_URL',
        'mysql+pymysql://root:120110@localhost:3306/community_repair'
    )

    # 关闭 SQLAlchemy 的修改追踪功能（节省内存）
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ============================================
    # JWT 配置（用户登录 Token）
    # ============================================

    # JWT 密钥
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-in-production')

    # Token 过期时间：7天
    # 用户登录后 7 天内不需要重新登录
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(days=7)

    # ============================================
    # 微信小程序配置
    # ============================================

    # 小程序的 AppID 和 AppSecret
    # 需要在微信公众平台注册小程序后获取
    WECHAT_APP_ID = os.getenv('WECHAT_APP_ID', '')
    WECHAT_APP_SECRET = os.getenv('WECHAT_APP_SECRET', '')
    # ============================================
    # 微信订阅消息配置（通知）
    # ============================================

    # 工单状态变更通知模板ID（通知报修居民）
    WECHAT_STATUS_TEMPLATE_ID = os.getenv('WECHAT_STATUS_TEMPLATE_ID', '')

    # 新工单分配通知模板ID（通知维修人员）
    WECHAT_ASSIGN_TEMPLATE_ID = os.getenv('WECHAT_ASSIGN_TEMPLATE_ID', '')


    # ============================================
    # 文件上传配置
    # ============================================

    # 上传文件保存目录
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'uploads')

    # 允许上传的图片格式
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

    # 最大上传文件大小：5MB
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024


class DevelopmentConfig(Config):
    """开发环境配置"""

    # 开启调试模式：代码修改后自动重启，显示详细错误信息
    DEBUG = True


class ProductionConfig(Config):
    """生产环境配置"""

    # 关闭调试模式：更安全
    DEBUG = False


# 配置映射表
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
