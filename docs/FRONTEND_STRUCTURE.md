# 小巧的工具箱前端结构说明

本文档说明 `toolbox` 项目前端 UniApp 工程的目录结构、核心入口、页面组织方式、主题系统、构建产物和常用开发命令。

前端项目路径：

```text
/home/ubuntu/toolbox-project/frontend
```

## 1. 整体目录结构

```text
frontend/
├── package.json                 # 前端依赖和 npm scripts
├── package-lock.json            # npm 锁文件
├── index.html                   # H5 入口 HTML
├── src/                         # UniApp 源码目录
│   ├── main.ts                  # Vue/UniApp 应用入口
│   ├── App.vue                  # 应用根组件，全局生命周期和全局样式入口
│   ├── pages.json               # UniApp 页面路由和导航栏配置
│   ├── manifest.json            # UniApp 应用配置
│   ├── uni.scss                 # 全局样式、主题变量、通用组件样式
│   ├── pages/                   # 页面目录
│   │   ├── index/
│   │   │   └── index.vue        # 首页
│   │   ├── weather/
│   │   │   └── index.vue        # 天气预报页
│   │   ├── oil-price/
│   │   │   └── index.vue        # 油价查询页
│   │   ├── qrcode/
│   │   │   └── index.vue        # 二维码生成页
│   │   └── password/
│   │       └── index.vue        # 密码生成器页
│   ├── components/
│   │   └── ThemeSwitcher.vue    # 主题切换组件
│   ├── utils/
│   │   ├── theme.ts             # 主题列表、主题切换、主题持久化
│   │   ├── location.ts          # 定位相关工具
│   │   └── location-format.ts   # 定位信息格式化工具
│   ├── api/
│   │   └── index.ts             # API 请求封装
│   └── static/
│       └── logo.png             # 源码静态资源
├── public/                      # H5 SEO 静态文件源码
│   ├── robots.txt
│   ├── sitemap.xml
│   ├── weather.html
│   ├── oil-price.html
│   ├── qrcode.html
│   └── password.html
├── scripts/                     # 辅助脚本和测试脚本
│   ├── copy-seo-static.mjs      # H5 构建后复制 public SEO 文件
│   ├── test-location-format.mjs
│   ├── test-oil-price-page.mjs
│   ├── test-weather-page.mjs
│   └── test-theme.mjs
└── dist/
    └── build/
        ├── h5/                  # H5 编译产物
        └── mp-weixin/           # 微信小程序编译产物
```

## 2. 应用启动流程

### 2.1 `src/main.ts`

`main.ts` 是应用入口，使用 Vue 3 的 `createSSRApp` 创建应用：

```ts
import { createSSRApp } from "vue";
import App from "./App.vue";

export function createApp() {
  const app = createSSRApp(App);
  return { app };
}
```

整体启动链路：

```text
main.ts
  ↓
App.vue
  ↓
pages.json 注册页面
  ↓
pages/*/index.vue 页面组件
  ↓
components / utils / api
```

### 2.2 `src/App.vue`

`App.vue` 是全局根组件，目前主要负责：

1. 在 `onLaunch` 生命周期里初始化主题。
2. 引入全局样式 `uni.scss`。

```vue
<script setup lang="ts">
import { onLaunch } from '@dcloudio/uni-app'
import { initTheme } from '@/utils/theme'

onLaunch(() => {
  initTheme()
})
</script>

<style>
@import './uni.scss';
</style>
```

## 3. 页面路由结构

UniApp 使用 `src/pages.json` 注册页面。当前页面列表：

| 页面 | 路径 | 说明 |
| --- | --- | --- |
| 首页 | `pages/index/index` | 工具首页、搜索、分类、热门工具入口 |
| 油价查询 | `pages/oil-price/index` | 查询各省汽柴油价格 |
| 二维码生成 | `pages/qrcode/index` | 文本 / 网址生成二维码 |
| 密码生成器 | `pages/password/index` | 生成随机安全密码 |
| 天气预报 | `pages/weather/index` | 查询城市天气和预报 |

对应源码文件：

```text
src/pages/index/index.vue
src/pages/oil-price/index.vue
src/pages/qrcode/index.vue
src/pages/password/index.vue
src/pages/weather/index.vue
```

每个页面通常由三部分组成：

```vue
<template>
  <!-- 页面结构 -->
</template>

<script setup lang="ts">
// 页面逻辑
</script>

<style scoped>
/* 页面私有样式 */
</style>
```

## 4. 首页结构

首页源码：

```text
src/pages/index/index.vue
```

首页主要模块：

1. `ThemeSwitcher` 主题切换按钮。
2. Hero 顶部介绍区。
3. 搜索框。
4. 三个卖点卡片：
   - 🎁 免费使用
   - 🧰 常用工具
   - 📱 跨端
5. 快捷入口 / 热门工具列表。
6. 全部工具分类浏览。
7. 底部页脚和 ICP 备案号。

首页中的工具列表目前在页面内维护：

```ts
const tools = ref<ToolItem[]>([
  // oil-price / weather / qrcode / password / base64 / url / json ...
])
```

其中：

- `implemented: true` 表示已实现，可点击进入。
- `implemented: false` 表示规划中或即将上线。
- `badge` 用于热门、常用、安全等标记。
- `category` 用于分类过滤。

## 5. 主题系统

主题逻辑位于：

```text
src/utils/theme.ts
```

当前支持主题：

| id | 名称 | className |
| --- | --- | --- |
| `light` | 默认浅色 | `theme-light` |
| `warm` | 暖阳橙 | `theme-warm` |
| `fresh` | 清新绿 | `theme-fresh` |
| `minimal` | 极简灰 | `theme-minimal` |
| `night` | 暗夜蓝 | `theme-night` |

页面使用方式：

```ts
const { themeClass } = useTheme()
```

模板根节点绑定：

```vue
<view :class="['container', themeClass]">
```

全局主题变量定义在：

```text
src/uni.scss
```

例如暗夜蓝主题：

```scss
.container.theme-night {
  --theme-primary: #60a5fa;
  --theme-bg: linear-gradient(180deg, #0f172a 0%, #111827 52%, #020617 100%);
  --theme-surface: rgba(15, 23, 42, 0.9);
  --theme-text: #e5eefc;
  --theme-text-secondary: #cbd5e1;
  --theme-text-muted: #94a3b8;
}
```

如果是全局主题色、通用卡片、通用文字对比度，优先改 `src/uni.scss`。

如果是某个页面独有的视觉细节，例如首页卖点卡片，优先改该页面的 `style scoped`。

## 6. 公共组件

当前公共组件目录：

```text
src/components/
└── ThemeSwitcher.vue
```

`ThemeSwitcher.vue` 是主题切换组件，会调用 `utils/theme.ts` 中的主题选择逻辑。

如果后续有多个页面共用的 UI，建议放到 `src/components/`。

## 7. 工具函数和 API

### 7.1 `src/api/index.ts`

用于封装后端 API 请求。天气、油价等需要后端数据的页面，通常通过这里调用接口。

### 7.2 `src/utils/location.ts`

定位相关逻辑。

### 7.3 `src/utils/location-format.ts`

定位结果格式化逻辑。

### 7.4 `src/utils/theme.ts`

主题列表、主题切换、主题持久化逻辑。

## 8. H5 SEO 静态页

目录：

```text
frontend/public/
```

当前包含：

```text
robots.txt
sitemap.xml
weather.html
oil-price.html
qrcode.html
password.html
```

这些页面是给搜索引擎抓取用的静态落地页，不替代 UniApp 的真实工具页。

静态页一般会提供：

- title
- meta description
- meta keywords
- canonical
- 正文说明
- FAQ
- 指向 UniApp hash 路由的 CTA 链接

例如：

```text
https://quan1234.com/qrcode.html
  ↓ CTA
https://quan1234.com/#/pages/qrcode/index
```

注意：本项目的 `uni build` 不会自动复制 `frontend/public/*` 到 `frontend/dist/build/h5/`，所以构建脚本额外执行：

```json
"build:h5": "uni build && node scripts/copy-seo-static.mjs"
```

复制逻辑在：

```text
frontend/scripts/copy-seo-static.mjs
```

## 9. 构建产物

构建产物目录：

```text
frontend/dist/build/
├── h5/          # H5 网站产物
└── mp-weixin/   # 微信小程序产物
```

### 9.1 H5 产物

```text
frontend/dist/build/h5/
```

用于网站部署。

里面包含：

- `index.html`
- `assets/`
- `static/`
- SEO 静态文件：`robots.txt`、`sitemap.xml`、`weather.html` 等

### 9.2 微信小程序产物

```text
frontend/dist/build/mp-weixin/
```

用于导入微信开发者工具或上传小程序。

里面包含：

- `app.js`
- `app.json`
- `app.wxss`
- `pages/*/*.wxml`
- `pages/*/*.wxss`
- `pages/*/*.js`
- `common/vendor.js`

## 10. 常用命令

进入前端目录：

```bash
cd /home/ubuntu/toolbox-project/frontend
```

开发 H5：

```bash
npm run dev:h5
```

类型检查：

```bash
npm run type-check
```

构建 H5：

```bash
npm run build:h5
```

构建微信小程序：

```bash
npm run build:mp-weixin
```

运行项目测试脚本：

```bash
npm test
```

## 11. 提交约定

本项目当前约定：

1. 修改代码前先同步远程：

```bash
git pull --ff-only
```

2. 前端源码改动后，通常需要同步构建并提交产物：

```bash
cd frontend
npm run type-check
npm run build:h5
npm run build:mp-weixin
```

3. 提交内容通常包括：

```text
frontend/src/...                  # 源码
frontend/dist/build/h5/...        # H5 产物
frontend/dist/build/mp-weixin/... # 小程序产物
```

4. 不提交 `.zip` 文件，例如：

```text
frontend/dist/build/toolbox-miniprogram.zip
```

5. 每次 commit 后推送到远程：

```bash
git push origin master
```

## 12. 常见修改位置

| 需求 | 推荐修改位置 |
| --- | --- |
| 修改首页 UI | `src/pages/index/index.vue` |
| 新增工具页面 | `src/pages/<tool-name>/index.vue` + `src/pages.json` |
| 修改主题颜色 | `src/uni.scss` 和 `src/utils/theme.ts` |
| 修改主题切换按钮 | `src/components/ThemeSwitcher.vue` |
| 修改 API 地址或请求方法 | `src/api/index.ts` |
| 修改 H5 SEO 静态页 | `frontend/public/*.html` |
| 修改 H5 SEO 文件复制逻辑 | `frontend/scripts/copy-seo-static.mjs` |
| 修改微信小程序配置 | `src/project.config.json` / `src/project.private.config.json` |

## 13. 新增工具页面建议流程

1. 在 `src/pages/` 下新增页面目录，例如：

```text
src/pages/base64/index.vue
```

2. 在 `src/pages.json` 中注册页面：

```json
{
  "path": "pages/base64/index",
  "style": {
    "navigationBarTitleText": "Base64 编码解码",
    "navigationBarBackgroundColor": "#007aff",
    "navigationBarTextStyle": "white"
  }
}
```

3. 在首页 `src/pages/index/index.vue` 的 `tools` 列表中修改或新增工具项。

4. 如需后端数据，在 `src/api/index.ts` 中封装请求。

5. 如需 SEO 静态页，在 `frontend/public/` 下新增对应 HTML，并更新 `sitemap.xml`。

6. 执行检查和构建：

```bash
cd frontend
npm run type-check
npm run build:h5
npm run build:mp-weixin
```

7. 提交源码和构建产物。
