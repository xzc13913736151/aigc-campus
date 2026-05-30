# CampusClaw

CampusClaw 是一个微信小程序校园社交与协作平台，包含论坛、组队匹配、恋爱匹配、交易匹配、聊天、个人资料、黑名单、举报审核和 AI 助手能力。

当前项目用于比赛演示，推荐使用“电脑本地后端 + 手机同 Wi-Fi 预览”的方式运行。

## 目录

- [一、项目结构](#一项目结构)
- [二、比赛演示启动方式](#二比赛演示启动方式)
- [三、小程序构建与预览](#三小程序构建与预览)
- [四、常见问题](#四常见问题)
- [五、上线前说明](#五上线前说明)

## 一、项目结构

```text
aigc-campus-main/
  apps/
    api/                 # Django 后端
    mp/                  # uni-app 微信小程序
  docs/                  # 项目文档
  config.yaml            # AI 大模型配置
  docker-compose.yml     # 可选数据库/Redis 配置
```

关键目录：

```text
apps/api                 # 后端根目录
apps/mp/src              # 小程序源码
apps/mp/dist/build/mp-weixin  # 小程序构建产物，微信开发者工具导入这里
```

## 二、比赛演示启动方式

### 1. 确认小程序请求地址

当前小程序后端地址已配置为你的电脑局域网 IP：

```ts
export const BASE_URL = "http://10.130.55.19:8000/api/v1";
```

配置文件位置：

```text
apps/mp/src/constants/index.ts
```

如果你换了 Wi-Fi，电脑 IPv4 可能会变，需要重新运行：

```powershell
ipconfig
```

找到当前 Wi-Fi 的 IPv4 地址，然后把 `BASE_URL` 改成新的地址。

### 2. 启动后端

在项目根目录运行：

```powershell
conda activate aigc
$env:DEBUG='1'
$env:SECRET_KEY='campusclaw-local-dev-secret'
$env:ALLOWED_HOSTS='localhost,127.0.0.1,10.130.55.19'
python apps/api/manage.py runserver 0.0.0.0:8000
```

如果你已经在 `apps/api` 目录，运行：

```powershell
conda activate aigc
$env:DEBUG='1'
$env:SECRET_KEY='campusclaw-local-dev-secret'
$env:ALLOWED_HOSTS='localhost,127.0.0.1,10.130.55.19'
python manage.py runserver 0.0.0.0:8000
```

注意：这里必须是 `0.0.0.0:8000`，不要用 `127.0.0.1:8000`。否则手机访问不到电脑上的后端。

### 3. 验证后端能被手机访问

电脑浏览器先打开：

```text
http://10.130.55.19:8000/health/
```

手机和电脑连同一个 Wi-Fi 后，手机浏览器也打开：

```text
http://10.130.55.19:8000/health/
```

如果看到：

```json
{ "status": "ok" }
```

说明手机已经能连到后端。

如果手机浏览器打不开，优先检查：

- 手机和电脑是否在同一个 Wi-Fi。
- 手机是否关掉了流量，只使用 Wi-Fi。
- Django 是否用 `0.0.0.0:8000` 启动。
- Windows 防火墙是否允许 Python 访问专用网络。
- 当前电脑 IPv4 是否还是 `10.130.55.19`。

### 4. 首次初始化数据库

第一次运行项目，或者数据库为空时，在项目根目录执行：

```powershell
conda activate aigc
$env:DEBUG='1'
$env:SECRET_KEY='campusclaw-local-dev-secret'
python apps/api/manage.py migrate
```

如需创建 Django 管理员账号：

```powershell
python apps/api/manage.py createsuperuser
```

## 三、小程序构建与预览

### 1. 安装前端依赖

项目根目录运行：

```powershell
cmd /c npx pnpm install
```

### 2. 构建微信小程序

项目根目录运行：

```powershell
cmd /c npx pnpm --dir apps/mp build:mp-weixin
```

或

```powershell
cmd /c npx pnpm --dir apps/mp dev:mp-weixin
```

构建完成后，微信开发者工具导入：

```text
apps/mp/dist/build/mp-weixin
```

或

```text
apps/mp/dist/dev/mp-weixin
```

### 3. 微信开发者工具设置

比赛演示时需要在微信开发者工具勾选：

```text
详情 -> 本地设置 -> 不校验合法域名、web-view、TLS 版本以及 HTTPS 证书
```

然后点击“编译”，再扫码预览。

### 4. 演示时需要保持打开

比赛演示时，电脑上至少保持这些东西开着：

- Django 后端终端。
- 微信开发者工具。
- 如果要演示 AI，确保 `config.yaml` 中的大模型配置可用。

电脑不能关机，后端终端不能关闭。

## 四、常见问题

### 1. 手机登录或请求一直失败

先用手机浏览器打开：

```text
http://10.130.55.19:8000/health/
```

如果浏览器都打不开，就是局域网、IP、防火墙或后端监听问题。

如果浏览器能打开，但小程序不行，检查：

- `apps/mp/src/constants/index.ts` 里的 `BASE_URL` 是否正确。
- 微信开发者工具是否勾选“不校验合法域名”。
- 修改 `BASE_URL` 后是否重新构建小程序。

### 2. 换 Wi-Fi 后不能用了

电脑 IPv4 可能变了。重新运行：

```powershell
ipconfig
```

然后更新：

```text
apps/mp/src/constants/index.ts
```

再重新构建：

```powershell
cmd /c npx pnpm --dir apps/mp build:mp-weixin
```

### 3. AI 对话失败

检查根目录的：

```text
config.yaml
```

需要配置可用的大模型：

```yaml
agent:
  api_key: "你的 key"
  base_url: "你的 base url"
  model: "模型名"
```

如果网络慢，AI 可能会等待较久。当前前端已给 AI 请求设置较长超时时间。

### 4. 图片不显示

本地演示使用 HTTP，微信开发者工具可能会提示 HTTPS 警告。比赛演示时勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”即可。

### 5. 修改代码后小程序没变化

执行：

```powershell
cmd /c npx pnpm --dir apps/mp build:mp-weixin
```

然后在微信开发者工具点击“编译”。

如果还不变，微信开发者工具里执行：

```text
工具 -> 清除缓存 -> 全部清除
```

## 五、上线前说明

当前 README 主要服务比赛演示。如果以后要正式发布给所有用户，需要做这些事情：

- 把 Django 后端部署到公网服务器。
- 配置正式数据库。
- 准备域名和 HTTPS。
- 把 `BASE_URL` 改成线上 HTTPS API 地址。
- 在微信公众平台配置 request/upload/socket 合法域名。
- 完成小程序备案、隐私协议、用户协议和审核提交。

正式上线后，小程序前端由微信平台分发，不需要你的电脑一直开着；但后端服务器和数据库必须长期在线。
