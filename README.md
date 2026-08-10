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
apps/mp/dist/build/app           # App 构建产物，HBuilderX 可用于云打包 APK
```

## 比赛演示启动流程总览

这个项目现在可以走两条前端演示路线：

```text
路线 A：微信小程序
  pnpm 构建 mp-weixin -> 微信开发者工具导入 -> 真机预览

路线 B：Android APK
  HBuilderX 打包 APK -> 手机安装 APK -> 连接同一个后端
```

两条路线共用同一个 Django 后端。也就是说，**前端可以是小程序或 APK，但后端仍然需要启动，并且手机必须能访问到后端地址**。

## 一、通用准备：后端地址、数据库和后端服务

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

## 二、路线 A：运行微信小程序

### 6. 构建微信小程序

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

小程序根目录是：

```text
apps/mp/dist/build/mp-weixin
```

如果使用开发模式产物，则导入：

```text
apps/mp/dist/dev/mp-weixin
```

## 三、路线 B：打包 Android APK

### 7. 使用 HBuilderX 运行到 Android 手机或模拟器

如果需要把 uni-app 前端作为 Android App 运行或打 APK，使用 HBuilderX。

1. 下载 HBuilderX：

```text
https://www.dcloud.io/hbuilderx.html
```

建议下载 Windows 版的 App 开发版。安装后打开 HBuilderX，并登录 DCloud 账号。

2. 安装前端依赖：

```powershell
cd C:\Users\Lenovo\Desktop\aigc\aigc-campus-main\apps\mp
cmd /c npx pnpm install
```

3. 用 HBuilderX 打开源码项目：

```text
文件 -> 打开目录
C:\Users\Lenovo\Desktop\aigc\aigc-campus-main\apps\mp
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

当前项目更稳定的 APK 打包流程是用 HBuilderX 打开 `apps/mp` 源码目录，然后走云打包。

1. 确认 App 配置：

```text
apps/mp/src/manifest.json
```

当前已配置：

```text
应用名：CampusClaw
Android 包名：com.campusclaw.app
版本名称：0.1.0
版本号：100
```

2. 用 HBuilderX 打开源码目录：

```text
文件 -> 打开目录
C:\Users\Lenovo\Desktop\aigc\aigc-campus-main\apps\mp
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

### 9. APK 安装后如何运行

1. 电脑启动后端：

```powershell
conda activate aigc
python apps/api/manage.py runserver 0.0.0.0:8000
```

2. 手机和电脑连接同一个 Wi-Fi 或同一个手机热点。

3. 手机浏览器打开：

```text
http://当前电脑IPv4:8000/health/
```

4. 如果能看到：

```json
{ "status": "ok" }
```

5. 再打开手机上安装好的 CampusClaw APK。

注意：如果换了 Wi-Fi，电脑 IPv4 变了，需要重新修改 `apps/mp/src/constants/index.ts` 里的 `BASE_URL`，然后重新云打包并安装 APK。

## 四、哪种方式适合比赛

```text
只需要现场演示：
  微信小程序真机预览 或 APK 都可以，电脑现场启动后端。

比赛要求提交 APK：
  用 HBuilderX 云打包 APK，提交 APK 文件。

想让评委离开现场也能打开：
  需要把 Django 后端部署到公网服务器，并把 BASE_URL 改成公网 HTTPS 地址。
```

## 五、大模型应用与调用说明

本项目的大模型能力不是单纯聊天，而是嵌入到 CampusClaw 的业务闭环里，主要用于：

```text
1. 普通 AI 对话
2. 发帖、评论、组队、交易、个人资料等草稿生成
3. AI 动作卡片：填充并发布 / 仅填充 / 仅生成
4. 组队、恋爱、交易推荐
5. 联系 TA 的破冰话术生成
6. 推荐理由与推荐指数生成/组织
```

### 1. 大模型配置在哪里

大模型配置文件在项目根目录：

```text
config.yaml
```

示例：

```yaml
agent:
  api_key: "你的 key"
  base_url: "你的 base url"
  model: "模型名"
  endpoint_path: "/chat/completions"
  timeout_seconds: 30
  temperature: 0.7
  max_tokens: 800
```

也可以用环境变量覆盖：

```text
AGENT_API_KEY
AGENT_BASE_URL
AGENT_MODEL
AGENT_ENDPOINT_PATH
AGENT_TIMEOUT_SECONDS
AGENT_TEMPERATURE
AGENT_MAX_TOKENS
```

组队、恋爱和交易推荐使用 OpenAI 兼容的 embeddings 接口做向量匹配。至少还需要配置：

```text
AGENT_EMBEDDING_MODEL=你的向量模型名
AGENT_EMBEDDING_ENDPOINT_PATH=/embeddings
AGENT_VECTOR_MIN_SIMILARITY=0.25
```

默认复用 `AGENT_API_KEY` 和 `AGENT_BASE_URL`。如果向量模型来自另一个服务，再单独配置：

```text
AGENT_EMBEDDING_API_KEY=向量服务的 key
AGENT_EMBEDDING_BASE_URL=https://向量服务地址/v1
```

推荐请求会批量生成查询与候选内容的 embedding，在应用层计算余弦相似度并缓存结果。语义相似度占推荐分数的 85%，业务偏好和热度占 15%；性别、年龄范围、帖子状态和队伍容量仍作为硬条件。向量服务未配置或暂时不可用时，系统会自动降级到原有关键词规则。

### 2. 后端大模型调用入口在哪里

后端大模型底层调用在：

```text
apps/api/assistant/agent.py
```

主要函数：

```text
load_agent_config()      # 读取 config.yaml 或环境变量
call_agent()             # 调用 OpenAI 风格 /chat/completions 接口，返回文本
call_agent_json()        # 调用大模型并要求返回 JSON，用于结构化决策和草稿生成
```

也就是说，如果要检查“大模型到底怎么被调用”，优先看这个文件。

### 3. AI 会话主流程在哪里

AI 会话、意图判断、草稿生成和动作卡片生成的主逻辑在：

```text
apps/api/assistant/orchestrator.py
```

主要函数：

```text
plan_assistant_turn()
  # 每次用户给 AI 发消息时的总入口
  # 正常路径先调用大模型判断推荐、创建、修改或消息等意图
  # 大模型接口失败时不执行任何业务动作，避免关键词误判

plan_turn_with_agent()
  # 使用大模型判断用户意图、当前页面、缺失字段和下一步动作

_build_agent_decision_messages()
  # 组织给大模型的 system prompt / user prompt
  # 要求模型判断 intent、user_signal、payload_patch 等结构化信息

_build_payload_generation_messages()
  # 组织草稿生成 prompt
  # 让模型根据用户输入生成帖子、组队、交易、资料等表单字段
```

这个文件是“AI 怎么理解用户自然语言，并把它变成 CampusClaw 业务动作”的核心。

### 4. AI 推荐算法在哪里

组队、恋爱、交易推荐逻辑在：

```text
apps/api/assistant/recommendations.py
```

主要函数：

```text
build_recommendation_action()
  # 执行大模型选定的组队、恋爱或交易推荐意图

build_team_recommendations()
  # 组队推荐
  # 使用大模型整理的 query 做向量相似度与业务规则综合排序

build_dating_recommendations()
  # 恋爱推荐
  # 同时参考用户已保存的匹配偏好和本次输入
  # 过滤不可见资料、本人、已跳过对象，并计算推荐指数

build_trade_recommendations()
  # 交易推荐
  # 使用大模型整理的 query 匹配现有商品；不会把购买请求自动变成求购帖

build_icebreaker_action()
  # 联系破冰
  # 根据当前页面对象生成一条礼貌的私聊开场白
```

推荐原则：

```text
推荐对象必须来自真实数据库
AI 不编造帖子、用户或交易商品
每条推荐都带推荐指数和推荐理由
用户自己决定是否联系、收藏、申请或表达感兴趣
```

### 5. AI 动作工具和业务执行在哪里

AI 可执行动作白名单在：

```text
apps/api/assistant/skills.py
```

主要内容：

```text
SKILLS
  # AI 允许生成和执行的动作注册表
  # 包括发布帖子、评论、点赞、发布组队、申请组队、发布交易、收藏交易、发送私聊、保存资料等

execute_action()
  # 执行 AI 动作卡片
  # 会检查动作状态、是否过期、动作类型是否在白名单里
```

典型执行函数：

```text
execute_forum_post_create()        # AI 确认后发布论坛帖子
execute_forum_comment_create()     # AI 确认后发布评论
execute_forum_post_like()          # AI 确认后点赞帖子
execute_forum_comment_like()       # AI 确认后点赞评论
execute_team_post_create()         # AI 确认后发布组队招募
execute_team_apply()               # AI 确认后申请加入组队
execute_trade_post_create()        # AI 确认后发布交易帖子
execute_trade_favorite()           # AI 确认后收藏交易
execute_context_chat_message_send()# AI 确认后联系对方并发送私聊
execute_dating_signal()            # AI 确认后发送感兴趣/跳过信号
execute_profile_update()           # AI 确认后保存个人资料
```

这部分体现了项目的安全设计：**大模型不能自由调用任意接口，只能通过后端白名单动作执行，并且需要用户确认。**

### 6. AI 接口在哪里

AI 相关 API 在：

```text
apps/api/assistant/views.py
apps/api/assistant/urls.py
```

主要接口逻辑：

```text
AssistantMessageListCreateAPIView
  # 前端发送 AI 消息后，后端创建用户消息、调用 AI 主流程、保存 AI 回复和动作卡片

AssistantActionExecuteAPIView
  # 用户点击“填充并发布”后，执行某个 AI 动作卡片
```

### 7. 前端 AI 调用在哪里

前端请求 AI 接口的位置：

```text
apps/mp/src/services/assistant.ts
```

主要函数：

```text
sendAssistantMessage()
  # 发送用户输入给后端 AI 会话接口

executeAssistantAction()
  # 执行 AI 动作卡片
```

半屏 AI 弹层组件：

```text
apps/mp/src/components/assistant/AssistantSheet.vue
```

主要函数：

```text
handleSend()
  # 用户在半屏 AI 输入框发送消息

handleFillAction()
  # 用户点击“仅填充”，把 AI 草稿写入页面

handleRecommendationAction()
  # 用户点击推荐卡片里的联系、收藏、感兴趣、跳过等按钮

handleExecuteAction()
  # 用户确认执行 AI 动作
```

独立 AI 页面：

```text
apps/mp/src/pages/assistant/index.vue
```

AI 动作卡片展示组件：

```text
apps/mp/src/components/assistant/AssistantActionCard.vue
```

### 8. 一次完整 AI 调用链路

以“帮我发一条组队帖子”为例：

```text
用户在小程序 AI 输入框输入需求
  ↓
前端 sendAssistantMessage()
  ↓
后端 AssistantMessageListCreateAPIView
  ↓
orchestrator.py 的 plan_assistant_turn()
  ↓
agent.py 的 call_agent_json() 调用大模型
  ↓
大模型返回结构化意图和草稿字段
  ↓
后端生成 AssistantActionProposal 动作卡片
  ↓
前端 AssistantActionCard 展示三个选择
  ↓
用户选择：填充并发布 / 仅填充 / 仅生成
  ↓
如果选择填充并发布，前端 executeAssistantAction()
  ↓
后端 skills.py 的 execute_action()
  ↓
执行对应业务函数，例如 execute_team_post_create()
  ↓
写入数据库并返回跳转结果
```

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

- 大模型结合提示词和 few-shot 示例决定用户要搜索现有内容还是创建新内容，并生成独立检索 query。
- 意图路由不使用关键词匹配；大模型不可用时明确失败，不会自动发布或切换到本地意图规则。
- 组队、交易和恋爱推荐使用向量相似度排序；向量服务故障时才降级到关键词规则。
- 恋爱推荐还会参考用户已保存的匹配偏好。
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
