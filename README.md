# 🛠️ 小巧的工具箱

基于 UniApp + FastAPI 开发的多合一工具聚合平台，支持微信小程序、H5双端。

## ✨ 功能特性

### 生活服务
- ⛽ 油价查询 - 全国各省市今日油价
- 🌤️ 天气预报 - 实时天气查询
- 📅 黄历日历 - 今日宜忌查询

### 编码工具
- 📱 二维码生成
- 🔐 随机密码生成
- 🔤 Base64 编解码
- 🔗 URL 编解码
- 📋 JSON 格式化

## 🏗️ 技术栈

### 前端
- **框架**: UniApp (Vue3 + TypeScript + Vite)
- **支持平台**: 微信小程序、H5
- **UI**: Uni-UI 组件库

### 后端
- **框架**: FastAPI (Python)
- **数据来源**: 天行数据 API
- **缓存**: Redis（可选，降低API调用成本）
- **部署**: Docker / 直接运行

## 🚀 快速开始

### 1. 后端启动

```bash
cd backend

# 创建虚拟环境并安装依赖
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的天行数据 API Key

# 启动服务
python main.py
```

访问 API 文档: http://localhost:8000/docs

### 2. 前端启动

```bash
cd frontend

# 安装依赖
npm install

# H5 开发模式
npm run dev:h5

# 微信小程序开发模式
npm run dev:mp-weixin
```

## 🔑 配置说明

### 天行数据 API Key 申请

1. 访问 [天行数据官网](https://www.tianapi.com)
2. 注册账号，获取 API Key
3. 在 `backend/.env` 中配置 `TIANAPI_KEY`

### 免费额度

- 大部分接口: 100次/天 免费调用
- 超过限制后可购买付费套餐

## 📁 项目结构

```
toolbox-project/
├── backend/
│   ├── main.py              # FastAPI 主入口
│   ├── api/
│   │   ├── tianapi.py     # 天行数据 API 封装
│   │   └── tools.py         # 本地工具服务
│   ├── utils/
│   │   ├── cache.py         # Redis 缓存
│   │   └── http_client.py   # HTTP 请求封装
│   ├── config.py             # 配置文件
│   └── requirements.txt
└── frontend/
    ├── src/
    │   ├── pages/            # 各工具页面
    │   ├── api/              # API 封装
    │   └── App.vue
    └── package.json
```

## 📱 小程序发布

### H5 打包

```bash
cd frontend
npm run build:h5
```

### 微信小程序打包

```bash
cd frontend
npm run build:mp-weixin
```

然后使用微信开发者工具打开 `dist/build/mp-weixin` 目录

## 🐳 Docker 部署

```bash
# 后端 Docker 构建
cd backend
docker build -t toolbox-api .

# 启动容器
docker run -d -p 8000:8000 toolbox-api
```

## 📄 License

MIT

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！
