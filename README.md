# PairUp

PairUp 目前聚焦于一个客户端：微信小程序。

## 仓库结构

- `apps/api`：Django 后端 API、业务逻辑、Django Admin
- `apps/mp`：基于 uni-app + Vue 3 的微信小程序
- `docs/`：架构说明、开发记录、功能规划

## 技术栈

- 后端：Django 5.2、Django REST framework、SimpleJWT、Channels
- 数据：SQLite（本地可直接跑）/ PostgreSQL、Redis
- 客户端：uni-app、Vue 3、TypeScript

## 一、先决条件

本地建议具备：

- Python 3.12
- Node.js 20+ 或更高
- 微信开发者工具

当前项目在 Windows PowerShell 下，`pnpm / npm / npx` 可能会被 `.ps1` 执行策略拦住。  
如果你看到“禁止运行脚本”之类报错，请统一改用 `cmd /c ...` 方式执行。

## 二、后端启动

如果你已经有 conda 环境，例如 `aigc`，可以直接使用。

在项目根目录进入后端目录：

```powershell
conda activate aigc
cd apps/api
```

先给 Django 设置本地开发环境变量：

```powershell
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
```

然后执行迁移并启动：

```powershell
python manage.py migrate
python manage.py runserver
```

如果你需要创建管理员账号：

```powershell
python manage.py createsuperuser
```

后端启动后常用地址：

- API 根地址：`http://127.0.0.1:8000/api/v1/`
- Swagger 文档：`http://127.0.0.1:8000/api/docs/`
- Django Admin：`http://127.0.0.1:8000/admin/`

## 三、可选基础设施

如果你想启用 PostgreSQL 和 Redis，而不是本地 SQLite / 内存通道，可在项目根目录执行：

```powershell
docker compose up -d db redis
```

说明：

- 不启动 Docker 也可以先本地看效果
- 当前 Django 在未配置 PostgreSQL 时会自动退回 SQLite
- 当前 Channels 在未配置 Redis 时会自动退回内存通道

## 四、小程序启动

### 1. 安装依赖

在项目根目录执行：

```powershell
cmd /c corepack enable
cmd /c corepack pnpm install
```

如果你只是想验证 Node 工具链是否正常，也可以先试：

```powershell
cmd /c node -v
cmd /c npm -v
```

### 2. 启动微信小程序开发构建

在项目根目录执行：

```powershell
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin
```

也可以使用根目录脚本：

```powershell
cmd /c corepack pnpm dev:mp
```

### 3. 微信开发者工具导入目录

构建成功后，把下面这个目录导入微信开发者工具：

```text
apps/mp/dist/dev/mp-weixin
```

如果用绝对路径，就是：

```text
C:\Users\Lenovo\Desktop\aigc\aigc-campus-main\apps\mp\dist\dev\mp-weixin
```

注意区分：

- 小程序源码目录：`apps/mp`
- 微信开发者工具实际要打开的目录：`apps/mp/dist/dev/mp-weixin`

## 五、当前建议体验页面

导入小程序后，优先看这些页面：

- `/pages/auth/login`：微信登录
- `/pages/profile/index`：首次登录资料补全
- `/pages/messages/index`：消息中心
- `/pages/chat/index`：聊天页
- `/pages/forum/index`：论坛列表
- `/pages/forum/detail`：帖子详情、评论、举报
- `/pages/dating/index`：匹配、举报、拉黑
- `/pages/admin/index`：管理员举报处理页

## 六、常见问题

### 1. `pnpm` 找不到

如果 PowerShell 提示：

- `pnpm 无法识别`
- `npm.ps1 / npx.ps1 / pnpm.ps1 被禁止执行`

请不要直接输入 `pnpm ...`，改成：

```powershell
cmd /c corepack pnpm install
cmd /c corepack pnpm --dir apps/mp dev:mp-weixin
```

### 2. `createsuperuser` 报 `Set SECRET_KEY when DEBUG is False`

说明当前终端里还没设置开发环境变量。先执行：

```powershell
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
```

再执行：

```powershell
python manage.py createsuperuser
```

### 3. 微信登录是否必须配置真实 AppID

如果你要完整验证真实微信登录链路，需要你自己的小程序 `AppID` 和微信后台配置。  
如果只是先看页面效果、资料补全、论坛、匹配、聊天和管理台等功能，可以先把前后端跑起来再继续调。

## 七、补充说明

- `node_modules/` 是前端依赖目录，删掉后可通过重新安装恢复
- `docs/` 存放的是功能清单、架构说明、ADR 和开发过程文档
- 更多功能现状可查看：
  - `docs/待实现功能清单.md`
  - `docs/后端待实现功能清单.md`
