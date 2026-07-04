"""
公共接口
========
所有用户都可以访问的接口，如获取楼栋列表、维修类别列表等。
"""

import os
import uuid
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from flask_jwt_extended import jwt_required
from werkzeug.utils import secure_filename
from models import Building, RepairCategory

# 创建蓝图
common_bp = Blueprint('common', __name__)


@common_bp.route('/buildings', methods=['GET'])
@jwt_required()
def get_buildings():
    """
    获取楼栋列表

    返回所有楼栋信息，用于报修时选择位置。
    """

    buildings = Building.query.all()

    return jsonify({
        'code': 200,
        'data': [b.to_dict() for b in buildings]
    })


@common_bp.route('/categories', methods=['GET'])
@jwt_required()
def get_categories():
    """
    获取维修类别列表

    只返回启用状态的类别。
    """

    categories = RepairCategory.query.filter_by(status='active').all()

    return jsonify({
        'code': 200,
        'data': [c.to_dict() for c in categories]
    })


@common_bp.route('/upload/image', methods=['POST'])
@jwt_required()
def upload_image():
    """
    上传图片

    请求参数（form-data）：
    - file: 图片文件

    返回：
    - url: 图片访问地址

    为什么需要单独的上传接口？
    - 图片文件较大，和表单数据分开处理更高效
    - 可以先上传图片获取URL，再提交表单
    - 方便实现上传进度显示
    """

    # 检查是否有文件
    if 'file' not in request.files:
        return jsonify({'code': 400, 'message': '请选择要上传的图片'}), 400

    file = request.files['file']

    # 检查文件名是否为空
    if file.filename == '':
        return jsonify({'code': 400, 'message': '请选择要上传的图片'}), 400

    # 检查文件类型
    if not allowed_file(file.filename):
        return jsonify({'code': 400, 'message': '只支持 PNG、JPG、JPEG、GIF 格式的图片'}), 400

    # 生成安全的文件名
    # 使用 UUID 避免文件名冲突，保留原扩展名
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f'{uuid.uuid4().hex}.{ext}'

    # 按日期分目录存储
    date_folder = datetime.now().strftime('%Y%m%d')
    upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'], date_folder)

    # 确保目录存在
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    # 保存文件
    filepath = os.path.join(upload_folder, filename)
    file.save(filepath)

    # 返回图片访问URL
    # 实际部署时需要配置正确的域名
    image_url = f'/uploads/{date_folder}/{filename}'

    return jsonify({
        'code': 200,
        'message': '上传成功',
        'data': {
            'url': image_url
        }
    })


def allowed_file(filename):
    """
    检查文件类型是否允许

    参数：
        filename: 文件名

    返回：
        True 如果文件类型允许，否则 False
    """

    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    allowed = current_app.config.get('ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif'})

    return ext in allowed
