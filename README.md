# CampusClaw - 校园交友与协作平台

CampusClaw 是一个基于微信小程序的校园交友与协作平台，支持论坛、组队匹配、恋爱匹配、交易匹配等功能。

## 目录

- [一、先决条件](#一先决条件)
- [二、后端启动](#二后端启动)
- [三、小程序前端启动](#三小程序前端启动)
- [四、微信开发者工具配置](#四微信开发者工具配置)
- [五、验证功能是否正常](#五验证功能是否正常)
- [六、管理员账号与后台](#六管理员账号与后台)
- [七、常见问题](#七常见问题)

---

## 一、先决条件

开始之前，你需要安装以下软件：

### 1.1 Python 3.12+

官网下载：https://www.python.org/downloads/

安装时**务必勾选** "Add Python to PATH"

验证安装：

```powershell
python --version
```

### 1.2 Node.js 20+

官网下载：https://nodejs.org/

验证安装：

```powershell
node -v
npm -v
```

### 1.3 Anaconda（推荐）

官网下载：https://www.anaconda.com/download

创建项目环境：

```powershell
conda create -n pairup python=3.12 -y
conda activate pairup
```

### 1.4 微信开发者工具

官网下载：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

### 1.5 Git（可选）

官网下载：https://git-scm.com/download/win

---

## 二、后端启动

### 2.1 安装后端依赖

**方式一：使用 conda 环境（推荐）**

```powershell
# 激活 conda 环境
conda activate aigc

# 进入后端目录
cd apps/api

# 安装依赖
pip install django djangorestframework djangorestframework-simplejwt django-cors-headers channels channels-redis drf-spectacular Pillow dj-database-url psycopg2-binary redis django-filter

# 安装 ASGI 服务器（用于实时推送，必须）
pip install daphne
```

**方式二：直接安装（如果没有 conda）**

```powershell
cd apps/api
pip install -r requirements.txt
pip install daphne
```

### 2.2 创建数据库（首次需要）

```powershell
cd apps/api

# 设置环境变量（Windows PowerShell）
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'

# 创建数据库表
python manage.py migrate

# 可选：创建管理员账号
python manage.py createsuperuser
```

`createsuperuser` 创建的是本地数据库里的管理员账号，主要用于 Django Admin 和小程序内置审核台。创建时填写的 `Email` 和 `Password` 就是后续本地邮箱密码登录使用的账号。

### 2.3 启动后端服务

#### 方式一：普通模式（无实时推送，推荐新手）

```powershell
cd apps/api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
python manage.py runserver
```

启动成功后访问：

- API 地址：http://127.0.0.1:8000/api/v1/
- Swagger 文档：http://127.0.0.1:8000/api/docs/
- Django Admin：http://127.0.0.1:8000/admin/

#### 方式二：ASGI 模式（支持实时推送，必须）

**为什么要开这个？**

- 实时聊天消息推送
- 实时通知
- 正在输入提示
- 在线状态显示

```powershell
cd apps/api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

> **注意**：两种方式不能同时运行，端口都是 8000。

---

## 三、小程序前端启动

### 3.1 安装前端依赖

```powershell
# 在项目根目录（不是 apps/mp）
cmd /c corepack enable
cmd /c corepack pnpm install
```

### 3.2 构建小程序

uni-app 有两种构建模式：

| 模式     | 命令              | 产物目录               | 用途             |
| -------- | ----------------- | ---------------------- | ---------------- |
| 开发模式 | `dev:mp-weixin`   | `dist/dev/mp-weixin`   | 热重载，方便调试 |
| 生产模式 | `build:mp-weixin` | `dist/build/mp-weixin` | 压缩混淆，体积小 |

```powershell
# 开发模式（推荐，日常开发用）
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin

# 生产模式（发布时用）
cmd /c corepack pnpm --dir apps/mp build:mp-weixin
```

---

## 四、微信开发者工具配置

### 4.1 打开项目

1. 打开微信开发者工具
2. 点击"导入项目"
3. 选择目录：
   - 开发模式：`apps/mp/dist/dev/mp-weixin`
   - 生产模式：`apps/mp/dist/build/mp-weixin`
4. AppID 填你的小程序 AppID（测试号也可以）

### 4.2 重要配置

在微信开发者工具中：

1. **勾选"不校验合法域名"**（开发环境用）
   - 设置 → 详情 → 本地设置 → 勾选

2. **勾选"关闭域名校验"**（如果遇到问题）
   - 设置 → 通用设置 → 勾选

### 4.3 刷新最新代码

如果你改了代码但小程序没更新：

1. 确认运行的构建命令：
   - 运行 `dev:mp-weixin` → 打开 `dist/dev/mp-weixin`
   - 运行 `build:mp-weixin` → 打开 `dist/build/mp-weixin`

2. 在微信开发者工具中点击"编译"按钮

3. 如果还不行，清除缓存：
   - 工具 → 清除缓存 → 全部清除
   - 然后重新编译

---

## 五、验证功能是否正常

后端和小程序都启动后，测试以下地址：

### 5.1 后端 API 测试

在浏览器或 Postman 访问：

```
GET http://127.0.0.1:8000/api/v1/forum/posts/
```

如果返回帖子列表，说明后端正常。

### 5.2 小程序测试

1. 登录微信小程序
2. 进入"论坛"页面，看帖子列表
3. 进入"匹配" tab，选择任意匹配类型
4. 进入"我的"页面，确认登录状态

### 5.3 近期功能验证

- 头像、论坛图片、聊天图片上传：正常图片应成功；超大、非图片或不支持格式会返回中文错误。
- 聊天页：图片消息可点击预览；消息超过一屏后自动滚到底部；间隔超过 5 分钟会出现时间分割。
- 交易页：我的交易可以切换出售中、已预定、已完成、已关闭；非作者可举报交易。
- AI 助手：独立 AI 页和半屏 AI 会在新消息、思考气泡、动作卡片出现后稳定滚到底部。

---

## 六、管理员账号与后台

### 6.1 创建管理员账号

首次本地开发时执行：

```powershell
cd apps/api
python manage.py createsuperuser
```

如果你使用 conda 环境：

```powershell
conda run -n aigc python apps/api/manage.py createsuperuser
```

如果当前已经在 `apps/api` 目录：

```powershell
conda run -n aigc python manage.py createsuperuser
```

创建后的管理员满足 `role=admin` 和 `is_staff=True`，可以访问 Django Admin 和小程序审核台。

### 6.2 登录管理员账号

小程序登录页保留微信登录，同时提供“本地调试 / 管理员”的邮箱密码登录表单。

使用 `createsuperuser` 时填写的邮箱和密码登录即可。管理员账号会自动跳过普通用户资料补全，并优先进入小程序审核台。

### 6.3 管理员当前功能

- 查看举报统计：全部、待处理、处理中、已解决、已驳回。
- 筛选举报：论坛帖子、论坛评论、交易帖子。
- 处理举报：设为处理中、标记解决、驳回举报。
- 内容处理：删除违规论坛帖子、删除违规评论、关闭违规交易帖子。
- 操作日志：展示最近审核操作，例如删除帖子、删除评论、关闭交易。
- Django Admin 入口：可复制后台地址进入更完整的 Django 管理界面。

### 6.4 管理功能测试流程

1. 用普通账号发布一条交易帖子。
2. 用另一个非作者账号，或本地可用的测试账号，在交易页点击“举报”。
3. 用管理员邮箱密码登录小程序。
4. 进入“我的”页，点击“管理后台”。
5. 在审核台选择“交易举报”。
6. 点击“关闭交易并结案”。
7. 查看“最近审核操作”，确认出现“关闭交易帖子”。
8. 回到交易广场，确认被关闭的交易不再公开展示。

---

## 七、常见问题

### Q1: `pnpm` 命令找不到

Windows PowerShell 报错 "pnpm 无法识别"，改用：

```powershell
cmd /c corepack pnpm install
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin
```

### Q2: `python` 命令找不到

说明 Python 没添加到 PATH，重装 Python 时勾选 "Add Python to PATH"。

或者用完整路径：

```powershell
C:\Users\你的用户名\AppData\Local\Programs\Python\Python312\python.exe
```

### Q3: `pip` 命令找不到

```powershell
python -m pip install xxx
```

### Q4: `daphne` 安装失败

```powershell
pip install daphne
```

如果网络不行，用国内镜像：

```powershell
pip install daphne -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q5: 数据库报错 "no such table"

需要先迁移数据库：

```powershell
cd apps/api
python manage.py migrate
```

### Q6: WebSocket 连接失败（`ws://127.0.0.1:8000/ws/...`）

这是正常的，如果你没启动 ASGI 服务器（daphne）。**不影响发帖、匹配等核心功能**。

只是聊天不会有实时推送，需要手动刷新。

如果需要实时功能，启动时用：

```powershell
daphne -b 0.0.0.0 -p 8000 config.asgi:application
```

### Q7: 头像不显示（HTTP 警告）

微信要求 HTTPS，本地开发时可以用 HTTP，不影响功能。

### Q8: 修改代码后小程序没变化

1. 确认构建命令和打开的目录是否匹配
2. 点击微信开发者工具的"编译"按钮
3. 清除缓存：工具 → 清除缓存 → 全部清除

### Q9: 微信登录不了

需要配置真实的微信小程序 AppID：

- 小程序端：`apps/mp/src/manifest.json`
- 后端：`.env` 文件中的 `WECHAT_MINIAPP_APPID` 和 `WECHAT_MINIAPP_SECRET`

没有真实 AppID 的话，可以用测试号体验部分功能。

---

## 快速启动命令汇总

### 完整启动（带实时推送）

```powershell
# 终端 1：后端（带实时推送）
cd apps/api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
daphne -b 0.0.0.0 -p 8000 config.asgi:application

# 终端 2：前端
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin

# 终端 3：打开微信开发者工具，导入 dist/dev/mp-weixin 目录
```

### 简化启动（无实时推送）

```powershell
# 终端 1：后端
cd apps/api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
python manage.py runserver

# 终端 2：前端
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin

# 微信开发者工具导入 dist/dev/mp-weixin
```

---

## 项目结构

```
aigc-campus-main/
├── apps/
│   ├── api/              # Django 后端
│   │   ├── accounts/     # 用户账户
│   │   ├── assistant/    # AI 助手
│   │   ├── chat/        # 聊天
│   │   ├── common/      # 公共模型
│   │   ├── dating/      # 恋爱匹配
│   │   ├── forum/      # 论坛
│   │   ├── moderation/  # 内容审核
│   │   ├── notifications/  # 通知
│   │   ├── profiles/    # 用户资料
│   │   ├── teammates/   # 组队匹配
│   │   ├── trade/       # 交易匹配
│   │   └── config/     # 配置
│   └── mp/              # 微信小程序前端
│       └── src/
│           ├── pages/  # 页面
│           ├── components/  # 组件
│           ├── services/    # API 服务
│           └── utils/       # 工具
├── docs/                # 文档
└── docker-compose.yml   # Docker 配置
```

## 技术栈

- **后端**：Django 5.2、Django REST framework、SimpleJWT、Channels
- **数据库**：SQLite（开发）/ PostgreSQL（生产）
- **实时通信**：Django Channels + WebSocket
- **前端**：uni-app、Vue 3、TypeScript
- **小程序**：微信小程序

---

有任何问题欢迎提交 Issue！
