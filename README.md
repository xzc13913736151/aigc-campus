# CampusClaw

CampusClaw 是一个用于比赛演示的校园社交与协作小程序，包含论坛、组队匹配、恋爱匹配、交易匹配、消息聊天、个人资料、举报审核和 AI 助手能力。

当前推荐演示方式是：电脑本地运行 Django 后端，手机和电脑连接同一个 Wi-Fi，通过微信开发者工具真机预览小程序。

## 项目结构

```text
aigc-campus-main/
  apps/
    api/                 # Django 后端
    mp/                  # uni-app 微信小程序端
  docs/                  # 项目说明文档
  config.yaml            # AI 大模型配置
  docker-compose.yml     # 可选数据库/Redis 配置
```

关键目录：

```text
apps/api                         # 后端根目录
apps/mp/src                      # 小程序源码
apps/mp/dist/build/mp-weixin     # 小程序构建产物，微信开发者工具导入这里
```

## 比赛演示启动流程

### 1. 确认后端地址

当前小程序后端地址在：

```text
apps/mp/src/constants/index.ts
```

如果换了 Wi-Fi，电脑局域网 IP 可能会变。PowerShell 运行：

```powershell
ipconfig
```

找到当前 Wi-Fi 的 IPv4，例如 `10.54.173.45`，然后确保 `BASE_URL` 类似：

```ts
export const BASE_URL = "http://10.54.173.45:8000/api/v1";
```

### 1.1 切换 Wi-Fi 或手机热点后的 IPv4 更新流程

如果电脑换了 Wi-Fi、重新连接手机热点，或者手机热点重启，电脑拿到的 IPv4 可能会变化。只要 IPv4 变了，需要同步改三个地方：

1. PowerShell 运行：

```powershell
ipconfig
```

2. 找到这一段：

```text
无线局域网适配器 WLAN:
  IPv4 地址 . . . . . . . . . . . . : 10.xx.xx.xx
```

不要使用 VMware、CorpLink、Wintun、TAP 这些适配器的 IP，只看 `WLAN` 下面的 `IPv4 地址`。

3. 修改前端接口地址：

```text
apps/mp/src/constants/index.ts
```

例如：

```ts
export const BASE_URL = "http://10.54.173.45:8000/api/v1";
```

4. 把同一个 IP 写进项目根目录 `.env`：

```text
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.54.173.45
```

本地演示建议 `.env` 同时保持这些配置，避免每次手动输入环境变量：

```text
DJANGO_DEBUG=True
DB_ENGINE=sqlite
USE_INMEMORY_CHANNEL_LAYER=True
SERVE_MEDIA_FILES=True
```

5. 手机浏览器验证：

```text
http://10.54.173.45:8000/health/
```

看到 `{ "status": "ok" }` 后，再重新构建小程序或 App。  
注意：如果 APK 已经安装到手机上，`BASE_URL` 变了以后必须重新构建并重新安装 APK。

### 2. 初始化数据库

第一次运行，或者数据库为空时，在项目根目录执行：

```powershell
conda activate aigc
python apps/api/manage.py migrate
```

### 3. 生成比赛演示数据

为了让 AI 推荐、组队、交易、恋爱匹配都有内容可展示，建议运行：

```powershell
conda activate aigc
python apps/api/manage.py seed_demo_data
```

这个命令可以重复执行，不会无限复制同一批演示数据。

演示账号密码统一为：

```text
密码：demo123456
```

常用演示账号：

```text
demo_frontend@campusclaw.local
demo_backend@campusclaw.local
demo_product@campusclaw.local
demo_trade@campusclaw.local
```

聊天演示账号也会一起生成：

```text
demo_chat_design@campusclaw.local
demo_chat_photo@campusclaw.local
demo_chat_math@campusclaw.local
demo_chat_keyboard@campusclaw.local
demo_chat_runner@campusclaw.local
demo_chat_music@campusclaw.local
```

比赛演示时优先登录 `demo_frontend@campusclaw.local`，消息页会预置多条聊天会话，覆盖项目协作、组队、交易、恋爱匹配和校园活动等场景。

### 4. 启动后端

项目会自动读取根目录 `.env`，确认 `.env` 已包含：

```text
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1,10.54.173.45
DB_ENGINE=sqlite
USE_INMEMORY_CHANNEL_LAYER=True
SERVE_MEDIA_FILES=True
```

在项目根目录运行：

```powershell
conda activate aigc
python apps/api/manage.py runserver 0.0.0.0:8000
```

如果你已经在 `apps/api` 目录，则运行：

```powershell
conda activate aigc
python manage.py runserver 0.0.0.0:8000
```

注意必须使用 `0.0.0.0:8000`，不要用 `127.0.0.1:8000`。否则手机访问不到电脑上的后端。
如果手机访问 `/health/` 出现 `DisallowedHost`，说明 `.env` 里的 `DJANGO_ALLOWED_HOSTS` 没有包含当前电脑 IPv4，按 1.1 节重新更新 IP 后重启后端。

### 5. 验证手机能访问后端

电脑浏览器打开：

```text
http://10.54.173.45:8000/health/
```

手机和电脑连接同一个 Wi-Fi 后，手机浏览器也打开同一个地址。

如果看到：

```json
{ "status": "ok" }
```

说明手机已经能连到后端。

### 6. 构建小程序

项目根目录运行：

```powershell
cmd /c npx pnpm install
cmd /c npx pnpm --dir apps/mp build:mp-weixin
或
cmd /c npx pnpm --dir apps/mp dev:mp-weixin
```

微信开发者工具导入：

```text
apps/mp/dist/build/mp-weixin
或
apps/mp/dist/dev/mp-weixin
```

开发者工具里建议勾选：

```text
详情 -> 本地设置 -> 不校验合法域名、web-view、TLS 版本以及 HTTPS 证书
```

然后点击“编译”，再扫码真机预览。

### 7. 使用 HBuilderX 运行到 Android 手机或模拟器

如果需要把 uni-app 前端作为 Android App 运行或打 APK，使用 HBuilderX。

1. 下载 HBuilderX：

```text
https://www.dcloud.io/hbuilderx.html
```

建议下载 Windows 版的 App 开发版。安装后打开 HBuilderX，并登录 DCloud 账号。

2. 安装前端依赖：

```powershell
cd E:\Develop\Pycharm\PycharmData\AIGC\aigc-campus\apps\mp
npm install --registry=https://registry.npmmirror.com
```

3. 用 HBuilderX 打开源码项目：

```text
文件 -> 打开目录
E:\Develop\Pycharm\PycharmData\AIGC\aigc-campus\apps\mp
```

4. Android 手机开启 USB 调试：

```text
设置 -> 关于手机 -> 连续点击版本号/系统版本 7 次
设置 -> 开发者选项 -> 打开 USB 调试
```

用支持数据传输的数据线连接电脑。手机弹出授权时选择“允许 USB 调试”。

5. 运行到手机或模拟器：

```text
运行 -> 运行到手机或模拟器 -> 运行到 Android App 基座
```

如果 HBuilderX 提示缺少编译器模块，先确认已经在 `apps/mp` 目录执行过 `npm install`。如果仍然失败，可以使用下面的 App 构建产物方式。

### 8. 构建 Android App 产物并云打包 APK

当前项目更稳定的 APK 打包流程是先命令行构建 App 产物，再用 HBuilderX 打包该产物目录。

1. 构建 App：

```powershell
cd E:\Develop\Pycharm\PycharmData\AIGC\aigc-campus\apps\mp
npm.cmd run build:app
```

2. 用 HBuilderX 打开 App 构建产物：

```text
文件 -> 打开目录
E:\Develop\Pycharm\PycharmData\AIGC\aigc-campus\apps\mp\dist\build\app
```

3. 云打包 APK：

```text
发行 -> App-Android/iOS-云打包
```

推荐配置：

```text
平台：Android
证书：使用云端证书
包名：com.campusclaw.app
版本名称：0.1.0
版本号：100
渠道包：无
打包方式：快速安心打包或传统打包
```

4. 查看打包状态并下载 APK：

```text
发行 -> App-Android/iOS-查看云打包状态
```

5. 安装 APK 前确认后端已启动，并且手机可以打开：

```text
http://当前电脑IPv4:8000/health/
```

APK 只包含前端，不包含 Django 后端。比赛现场演示时，电脑需要持续运行后端，手机和电脑需要连接同一个 Wi-Fi 或同一个手机热点。

## AI 演示口令

进入小程序 AI 助手后，可以测试：

```text
推荐几个前端组队
推荐二手键盘
推荐喜欢摄影的恋爱匹配
帮我写一句联系TA的话
帮我发一条关于比赛组队的帖子
帮我写一条评论
```

推荐逻辑说明：

- 组队和交易推荐主要根据你本次输入的关键词。
- 恋爱推荐会同时参考你保存的匹配偏好和本次输入。
- AI 只推荐数据库里真实存在的内容，不会编造推荐对象。
- 发布、评论、收藏、感兴趣等动作都需要用户确认。

## 常见问题

### 手机请求失败

先用手机浏览器打开：

```text
http://10.54.173.45:8000/health/
```

如果打不开，优先检查：

- 手机和电脑是否在同一个 Wi-Fi。
- Django 是否用 `0.0.0.0:8000` 启动。
- Windows 防火墙是否允许 Python 访问专用网络。
- `BASE_URL` 里的 IP 是否是当前电脑 IPv4。

### AI 对话失败

检查根目录：

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

如果网络慢，AI 回复可能等待较久。当前前端已经给 AI 请求设置较长超时时间。

### 图片不显示

本地演示使用 HTTP，微信开发者工具需要勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。小程序内的帖子图、头像和聊天图片已经做了本地缓存处理。

### 修改代码后小程序没变化

重新构建：

```powershell
cmd /c npx pnpm --dir apps/mp build:mp-weixin
```

然后微信开发者工具点击“编译”。如果仍不变化：

```text
工具 -> 清除缓存 -> 全部清除
```

## 正式上线说明

当前 README 主要服务比赛演示。如果以后要正式发布给所有用户，需要：

- 把 Django 后端部署到公网服务器。
- 配置正式数据库。
- 准备域名和 HTTPS。
- 把 `BASE_URL` 改成线上 HTTPS API 地址。
- 在微信公众平台配置 request/upload/socket 合法域名。
- 完成小程序备案、隐私协议、用户协议和审核提交。

正式上线后，小程序前端由微信平台分发，不需要你的电脑一直开着；但后端服务器和数据库必须长期在线。
