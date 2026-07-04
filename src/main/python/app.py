"""
Flask 应用工厂
==============
这个文件是整个后端的"入口"。

什么是应用工厂模式？
- 用一个函数来创建 Flask 应用
- 好处是可以创建多个应用实例（比如测试时用不同配置）
- 这是 Flask 推荐的最佳实践
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS

# 创建扩展实例（但还没有初始化）
# 这样其他文件可以导入这些对象
db = SQLAlchemy()  # 数据库
jwt = JWTManager()  # JWT 用户认证


def create_app(config_name=None):
    """
    创建并配置 Flask 应用

    参数:
        config_name: 配置名称，可选 'development' 或 'production'

    返回:
        配置好的 Flask 应用实例
    """

    # 创建 Flask 应用
    app = Flask(__name__)

    # 加载配置
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')

    from config import config
    app.config.from_object(config[config_name])

    # 初始化扩展
    db.init_app(app)  # 初始化数据库
    jwt.init_app(app)  # 初始化 JWT

    # 启用跨域支持
    # 这样微信小程序才能访问我们的接口
    CORS(app, resources={
        r"/api/*": {
            "origins": "*",  # 允许所有来源（生产环境应该限制）
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })

    # 确保上传目录存在
    upload_folder = app.config.get('UPLOAD_FOLDER')
    if upload_folder and not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 注册蓝图（路由模块）
    # 蓝图是 Flask 组织路由的方式，把不同功能的接口分开管理
    register_blueprints(app)

    # 注册错误处理
    register_error_handlers(app)

    return app


def register_blueprints(app):
    """
    注册所有蓝图（API 路由模块）

    什么是蓝图？
    - 蓝图是一种组织 Flask 路由的方式
    - 把相关的接口放在一起，比如所有认证相关的接口放在 auth 蓝图
    - 这样代码更清晰，更容易维护
    """

    from api import auth_bp, work_order_bp, admin_bp, super_bp, common_bp

    # 所有接口都以 /api/v1 开头
    # v1 表示 API 版本，以后升级可以用 v2
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(work_order_bp, url_prefix='/api/v1')
    app.register_blueprint(admin_bp, url_prefix='/api/v1/admin')
    app.register_blueprint(super_bp, url_prefix='/api/v1/super')
    app.register_blueprint(common_bp, url_prefix='/api/v1')


def register_error_handlers(app):
    """
    注册全局错误处理

    为什么需要错误处理？
    - 当出错时返回统一格式的 JSON 响应
    - 不会暴露敏感的错误信息
    - 前端可以统一处理错误
    """

    @app.errorhandler(400)
    def bad_request(error):
        """请求格式错误"""
        return {'code': 400, 'message': '请求格式错误'}, 400

    @app.errorhandler(401)
    def unauthorized(error):
        """未登录或 Token 无效"""
        return {'code': 401, 'message': '请先登录'}, 401

    @app.errorhandler(403)
    def forbidden(error):
        """没有权限"""
        return {'code': 403, 'message': '没有权限执行此操作'}, 403

    @app.errorhandler(404)
    def not_found(error):
        """资源不存在"""
        return {'code': 404, 'message': '请求的资源不存在'}, 404

    @app.errorhandler(500)
    def internal_error(error):
        """服务器内部错误"""
        return {'code': 500, 'message': '服务器内部错误，请稍后重试'}, 500
