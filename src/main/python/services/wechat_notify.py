"""微信通知服务
===========
负责发送微信订阅消息通知。
当工单状态变更时，向相关用户发送模板消息。

使用前需要在 settings.py 中配置：
    - WECHAT_APP_ID: 小程序AppID
    - WECHAT_APP_SECRET: 小程序AppSecret
    - WECHAT_STATUS_TEMPLATE_ID: 状态变更模板ID
    - WECHAT_ASSIGN_TEMPLATE_ID: 新工单分配模板ID

用户需先在小程序内通过 wx.requestSubscribeMessage 订阅对应模板。
"""

import requests
import json
from flask import current_app
from datetime import datetime


def get_access_token(app):
    """获取微信接口调用凭证（access_token）

    使用 app_id 和 app_secret 调用微信 API 获取 access_token。
    Token 有效期为 2 小时（7200秒），每次调用都会重新获取。

    Returns:
        str: access_token，获取失败返回 None
    """
    app_id = app.config.get('WECHAT_APP_ID', '')
    app_secret = app.config.get('WECHAT_APP_SECRET', '')

    if not app_id or not app_secret:
        app.logger.warning('微信通知：未配置 WECHAT_APP_ID 或 WECHAT_APP_SECRET')
        return None

    url = 'https://api.weixin.qq.com/cgi-bin/token'
    params = {
        'grant_type': 'client_credential',
        'appid': app_id,
        'secret': app_secret
    }

    try:
        resp = requests.get(url, params=params, timeout=10)
        result = resp.json()
        if 'access_token' in result:
            return result['access_token']
        else:
            app.logger.error(f'获取 access_token 失败: {result}')
            return None
    except Exception as e:
        app.logger.error(f'获取 access_token 异常: {e}')
        return None


def send_subscribe_message(app, openid, template_id, data, page=''):
    """发送微信订阅消息

    Args:
        openid: 接收消息的用户openid
        template_id: 消息模板ID（从微信公众平台获取）
        data: 模板数据，格式 {"keyword": {"value": "内容"}}
        page: 点击消息后跳转的小程序页面路径

    Returns:
        bool: 发送成功返回 True，失败返回 False
    """
    if not openid or not template_id:
        return False

    token = get_access_token(app)
    if not token:
        return False

    url = f'https://api.weixin.qq.com/cgi-bin/message/subscribe/send'
    payload = {
        'touser': openid,
        'template_id': template_id,
        'page': page,
        'data': data,
        'miniprogram_state': 'developer'  # developer/trial/formal
    }

    try:
        resp = requests.post(
            f'{url}?access_token={token}',
            json=payload,
            timeout=10
        )
        result = resp.json()
        if result.get('errcode') == 0:
            app.logger.info(f'微信通知发送成功: {openid}')
            return True
        else:
            app.logger.error(f'微信通知发送失败: {result}')
            return False
    except Exception as e:
        app.logger.error(f'微信通知发送异常: {e}')
        return False


def notify_order_status_change(app, order):
    """发送工单状态变更通知给报修居民

    当工单状态变化时（pending -> assigned -> processing -> completed），
    通知提交该工单的居民。

    Args:
        order: WorkOrder 实例（需已关联 user 关系）
    """
    if not order or not order.user:
        return False

    template_id = app.config.get('WECHAT_STATUS_TEMPLATE_ID', '')
    if not template_id:
        app.logger.warning('微信通知：未配置 WECHAT_STATUS_TEMPLATE_ID')
        return False

    status_names = {
        'pending': '待审核',
        'assigned': '已分配',
        'processing': '处理中',
        'completed': '已完成',
        'evaluated': '已评价'
    }

    status_descs = {
        'assigned': '维修人员已分配，请耐心等待',
        'processing': '维修人员正在处理中',
        'completed': '维修已完成，请进行评价',
        'evaluated': '感谢您的评价'
    }

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    new_status_name = status_names.get(order.status, order.status)
    desc = status_descs.get(order.status, f'状态已更新为: {new_status_name}')

    data = {
        'thing1': {'value': f'工单编号: {order.order_no}'},
        'thing2': {'value': desc},
        'time3': {'value': now}
    }

    page = f'pages/order-detail/order-detail?id={order.id}'

    return send_subscribe_message(app, order.user.openid, template_id, data, page)


def notify_assign_notification(app, order):
    """发送新工单分配通知给维修人员

    当管理员将工单分配给维修人员时，通知该维修人员。

    Args:
        order: WorkOrder 实例（需已关联 repairman 关系）
    """
    if not order or not order.repairman:
        return False

    template_id = app.config.get('WECHAT_ASSIGN_TEMPLATE_ID', '')
    if not template_id:
        app.logger.warning('微信通知：未配置 WECHAT_ASSIGN_TEMPLATE_ID')
        return False

    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    data = {
        'thing1': {'value': f'工单编号: {order.order_no}'},
        'thing2': {'value': f'来自: {order.user.name if order.user else "未知"}'},
        'thing3': {'value': order.description[:20] if order.description else '无描述'},
        'time4': {'value': now}
    }

    page = f'pages/repairman/order-detail/order-detail?id={order.id}'

    return send_subscribe_message(app, order.repairman.openid, template_id, data, page)