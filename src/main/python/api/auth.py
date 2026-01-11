"""
认证接口
========
处理用户登录、获取用户信息等认证相关操作。

微信小程序登录流程：
1. 小程序调用 wx.login() 获取 code
2. 小程序把 code 发给我们的后端
3. 后端用 code 调用微信服务器，换取用户的 openid
4. 后端根据 openid 查找或创建用户
5. 后端生成 JWT Token 返回给小程序
6. 之后小程序每次请求都带着这个 Token
"""

import requests
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import (
    create_access_token,
    jwt_required,
    get_jwt_identity
)
from ..app import db
from ..models import User

# 创建蓝图
# 蓝图名称 'auth'，URL 前缀在 app.py 中设置为 '/api/v1/auth'
auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    微信小程序登录

    请求参数（JSON）：
    - code: 微信登录凭证（必填）
    - name: 用户昵称（选填，首次登录时使用）
    - phone: 手机号（选填）

    返回：
    - token: JWT 访问令牌
    - user: 用户信息
    """

    data = request.get_json()

    if not data:
        return jsonify({'code': 400, 'message': '请求数据不能为空'}), 400

    code = data.get('code')
    if not code:
        return jsonify({'code': 400, 'message': '缺少登录凭证 code'}), 400

    # 调用微信服务器，用 code 换取 openid
    # 这一步是验证用户身份的关键
    openid = get_openid_from_wechat(code)

    if not openid:
        # 如果微信接口调用失败，为了方便开发测试，使用 code 作为 openid
        # 生产环境应该返回错误
        if current_app.debug:
            openid = f'debug_{code}'
        else:
            return jsonify({'code': 401, 'message': '微信登录失败'}), 401

    # 根据 openid 查找用户
    user = User.query.filter_by(openid=openid).first()

    if not user:
        # 新用户，创建账号
        name = data.get('name', '微信用户')
        phone = data.get('phone', '')

        user = User(
            openid=openid,
            name=name,
            phone=phone,
            role='resident',  # 默认是居民
            status='active'
        )
        db.session.add(user)
        db.session.commit()

    # 检查用户是否被禁用
    if user.status == 'disabled':
        return jsonify({'code': 403, 'message': '账号已被禁用'}), 403

    # 生成 JWT Token
    # identity 是 Token 中存储的用户标识，这里用用户ID
    access_token = create_access_token(identity=user.id)

    return jsonify({
        'code': 200,
        'message': '登录成功',
        'data': {
            'token': access_token,
            'user': user.to_dict()
        }
    })


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()  # 这个装饰器表示需要登录才能访问
def get_profile():
    """
    获取当前登录用户信息

    需要在请求头中带上 Token：
    Authorization: Bearer <token>
    """

    # 从 Token 中获取用户ID
    user_id = get_jwt_identity()

    # 查询用户
    user = User.query.get(user_id)
    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    return jsonify({
        'code': 200,
        'data': user.to_dict()
    })


@auth_bp.route('/profile', methods=['PUT'])
@jwt_required()
def update_profile():
    """
    更新当前用户信息

    请求参数（JSON）：
    - name: 姓名（选填）
    - phone: 手机号（选填）
    """

    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({'code': 404, 'message': '用户不存在'}), 404

    data = request.get_json()

    # 更新允许修改的字段
    if 'name' in data:
        user.name = data['name']
    if 'phone' in data:
        user.phone = data['phone']

    db.session.commit()

    return jsonify({
        'code': 200,
        'message': '更新成功',
        'data': user.to_dict()
    })


def get_openid_from_wechat(code):
    """
    调用微信服务器获取 openid

    参数：
        code: 小程序 wx.login() 返回的 code

    返回：
        openid 或 None
    """

    app_id = current_app.config.get('WECHAT_APP_ID')
    app_secret = current_app.config.get('WECHAT_APP_SECRET')

    if not app_id or not app_secret:
        # 没有配置微信参数，返回 None
        return None

    # 微信登录接口
    url = 'https://api.weixin.qq.com/sns/jscode2session'
    params = {
        'appid': app_id,
        'secret': app_secret,
        'js_code': code,
        'grant_type': 'authorization_code'
    }

    try:
        response = requests.get(url, params=params, timeout=10)
        result = response.json()

        if 'openid' in result:
            return result['openid']
        else:
            # 微信返回错误
            current_app.logger.error(f'微信登录失败: {result}')
            return None

    except Exception as e:
        current_app.logger.error(f'调用微信接口异常: {e}')
        return None
