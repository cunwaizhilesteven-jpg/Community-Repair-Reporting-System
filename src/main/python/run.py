"""
启动脚本
========
运行这个文件来启动后端服务器。

使用方法：
    python run.py

或者使用 Flask CLI：
    flask run
"""

from app import create_app

# 创建应用实例
app = create_app()

if __name__ == '__main__':
    # 启动开发服务器
    # host='0.0.0.0' 表示允许外部访问（小程序需要）
    # port=5000 是端口号
    # debug=True 是调试模式
    app.run(host='0.0.0.0', port=5000, debug=True)
