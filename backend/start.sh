#!/bin/bash
# 后端启动脚本

cd "$(dirname "$0")"

# 创建虚拟环境
if [ ! -d "venv" ]; then
    echo "创建 Python 虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
echo "安装依赖..."
pip install -r requirements.txt

# 复制配置文件
if [ ! -f ".env" ]; then
    echo "复制配置文件..."
    cp .env.example .env
    echo "⚠️ 请编辑 .env 文件，配置 TIANAPI_KEY"
fi

# 启动服务
echo "启动 API 服务..."
echo "访问地址: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"

python main.py
