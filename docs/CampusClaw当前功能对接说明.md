# CampusClaw 当前功能对接说明

更新时间：2026-05-17

本文档用于说明当前 CampusClaw 小程序与后端已经完成的联调内容、启动方式、接口约定和后续对接注意事项。

## 1. 项目结构

```text
aigc-campus/
  apps/
    api/                         # Django 后端
    mp/                          # uni-app 微信小程序源码
      src/                       # 小程序源代码
      dist/build/mp-weixin/      # 微信开发者工具导入目录
  docs/                          # 项目文档
```

微信开发者工具当前导入目录：

```text
apps/mp/dist/build/mp-weixin
```

小程序源码目录：

```text
apps/mp/src
```

后端目录：

```text
apps/api
```

## 2. 本地启动方式

### 2.1 启动后端

已创建本地 conda 环境：

```powershell
conda activate aigc
cd C:\Users\wenkx\Desktop\aigc-campus\apps\api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
python manage.py migrate
python manage.py runserver 127.0.0.1:8000
```

后端本地地址：

```text
http://127.0.0.1:8000
```

API 前缀：

```text
http://127.0.0.1:8000/api/v1
```

### 2.2 构建小程序

```powershell
cd C:\Users\wenkx\Desktop\aigc-campus
cmd /c corepack pnpm --dir apps/mp build:mp-weixin
```

构建完成后，在微信开发者工具中导入或刷新：

```text
apps/mp/dist/build/mp-weixin
```

如果微信开发者工具仍显示旧页面，执行：

```text
工具 -> 清除缓存 -> 清除编译缓存
```

然后重新编译。

## 3. 当前已完成内容

### 3.1 微信一键登录

当前已补全本地 demo 登录能力。

在 `DEBUG=1` 且未配置真实微信 `AppID` / `Secret` 时，后端会启用本地 demo 微信登录，不需要真实微信开放平台配置即可调试。

登录接口：

```http
POST /api/v1/auth/wechat-login/
```

请求示例：

```json
{
  "code": "demo-wechat-login-code"
}
```

返回内容包含：

```json
{
  "access": "...",
  "refresh": "...",
  "user": {
    "email": "wx_xxx@wechat.pairup.local",
    "nickname": "CampusClaw Demo"
  }
}
```

小程序端登录成功后会保存 token，并用于后续需要登录的接口。

注意：

- 微信开发者工具里如果请求本地后端，需要勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
- 本地小程序请求地址当前为 `http://127.0.0.1:8000/api/v1`。
- 真机调试时不能直接访问电脑的 `127.0.0.1`，需要换成电脑局域网 IP 或部署地址。

### 3.2 个人资料登录循环问题

已修复登录后在登录页和个人资料页之间循环跳转的问题。

修复点：

- 小程序端 token 状态改为响应式同步。
- 登录、刷新 token、清理登录态、启动恢复登录态时都会同步更新当前认证状态。

相关前端模块：

```text
apps/mp/src/utils/auth.ts
apps/mp/src/utils/wechat.ts
apps/mp/src/pages/auth/login.vue
```

### 3.3 发布帖子功能

当前论坛发布帖子已经从 demo 状态接入真实后端接口。

已完成：

- 新建帖子。
- 编辑已有帖子。
- 发布后自动刷新。
- 图片选择。
- 新帖子创建成功后自动上传图片。
- 编辑帖子时可追加图片。
- 登录态校验。
- 错误提示规整，避免显示内部变量名。

主要页面：

```text
apps/mp/src/pages/forum/create.vue
apps/mp/src/pages/forum/index.vue
apps/mp/src/pages/publish/index.vue
```

主要服务：

```text
apps/mp/src/services/forum.ts
apps/mp/src/utils/upload.ts
```

后端接口前缀：

```text
/api/v1/forum/
```

注意：

- “发布帖子”按钮已经改为普通 `view @tap` 触发，避免微信小程序原生 `button` 在复杂样式下出现不可点击或文字异常。
- 发布帖子需要登录。
- 图片上传依赖后端媒体接口和本地后端服务。

### 3.4 组队匹配功能

当前组队匹配功能已经接入真实后端，不再只是 demo。

已完成能力：

- 查看组队广场。
- 搜索招募。
- 发起组队招募。
- 查看“我的招募”。
- 编辑自己发布的招募。
- 关闭招募。
- 重新开放招募。
- 删除招募。
- 申请加入别人的招募。
- 查看我发出的申请。
- 查看我收到的申请。
- 通过或拒绝申请。
- 人数满员后自动标记为已招满。
- 防止重复申请。
- 防止申请自己的招募。
- 防止申请已关闭或已满员招募。

主要前端页面：

```text
apps/mp/src/pages/teammates/index.vue
```

发布表单组件：

```text
apps/mp/src/components/teammates/TeamComposer.vue
```

前端服务：

```text
apps/mp/src/services/teammates.ts
```

后端模块：

```text
apps/api/teammates/views.py
apps/api/teammates/serializers.py
apps/api/teammates/urls.py
apps/api/tests/test_teammates_api.py
```

组队相关接口：

```http
GET    /api/v1/teammates/posts/
POST   /api/v1/teammates/posts/
GET    /api/v1/teammates/posts/mine/
PATCH  /api/v1/teammates/posts/<post_id>/
DELETE /api/v1/teammates/posts/<post_id>/
POST   /api/v1/teammates/posts/<post_id>/apply/
GET    /api/v1/teammates/applications/mine/
GET    /api/v1/teammates/applications/received/
PATCH  /api/v1/teammates/applications/<application_id>/review/
```

发起组队请求示例：

```json
{
  "title": "找 2 位同学一起做 AI 校园工具项目",
  "summary": "希望找前端和设计同学一起做一个可上线的小工具",
  "details": "项目已有基础方向，希望补齐前端、设计和产品讨论，每周固定推进。",
  "target_size": 3,
  "tags": ["AI", "校园工具"],
  "required_skills": ["前端", "设计"]
}
```

重要交互说明：

- “发起组队”按钮只负责展开发布表单并滚动到表单位置。
- 真正请求后端的是表单底部的“发布组队”按钮。
- 如果看不到表单，优先确认小程序已经重新构建并清理编译缓存。
- 发起组队需要登录且个人资料已完善。

## 4. 当前本地联调配置

小程序 API 地址配置文件：

```text
apps/mp/src/constants/index.ts
```

当前配置：

```ts
export const BASE_URL = 'http://127.0.0.1:8000/api/v1'
```

后端本地调试环境变量：

```powershell
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
```

## 5. 验证命令

后端检查：

```powershell
cd C:\Users\wenkx\Desktop\aigc-campus\apps\api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
conda run -n aigc python manage.py check
```

组队功能测试：

```powershell
cd C:\Users\wenkx\Desktop\aigc-campus\apps\api
$env:DEBUG='1'
$env:SECRET_KEY='pairup-local-dev-secret'
conda run -n aigc python -m pytest tests/test_teammates_api.py
```

小程序构建：

```powershell
cd C:\Users\wenkx\Desktop\aigc-campus
cmd /c corepack pnpm --dir apps/mp build:mp-weixin
```

本地接口验证：

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:8000/api/v1/teammates/posts/ -Method Get
```

正常情况下空列表返回：

```json
[]
```

## 6. 常见问题

### 6.1 request fail 或 url not in domain list

处理方式：

- 微信开发者工具勾选“不校验合法域名、web-view、TLS 版本以及 HTTPS 证书”。
- 确认后端正在运行。
- 确认小程序 `BASE_URL` 是当前可访问地址。

### 6.2 Request failed with 500

处理方式：

- 先访问 `http://127.0.0.1:8000/api/v1/teammates/posts/` 判断后端是否正常。
- 查看后端终端报错。
- 已修复过组队列表空数据时 500 的问题，当前应返回 `200 []`。

### 6.3 点击“发起组队”没有直接发请求

这是正常交互。

“发起组队”只展开表单。填写表单后点击“发布组队”才会调用：

```http
POST /api/v1/teammates/posts/
```

### 6.4 登录后仍跳到登录页

处理方式：

- 清理微信开发者工具缓存。
- 重新登录。
- 确认本地后端使用 `DEBUG=1` 启动。
- 确认 `auth/wechat-login/` 返回了 `access` 和 `refresh`。

### 6.5 真机调试无法访问后端

原因：

```text
127.0.0.1 在真机上指向手机自己，不是电脑。
```

处理方式：

- 将 `BASE_URL` 改为电脑局域网 IP。
- 或使用部署后的 HTTPS 后端地址。

## 7. 对接人关注点

前端对接重点：

- 页面源码在 `apps/mp/src/pages`。
- 通用接口请求封装在 `apps/mp/src/utils/request.ts`。
- 登录态封装在 `apps/mp/src/utils/auth.ts`。
- 组队发布表单是独立组件 `TeamComposer.vue`。
- 修改源码后必须重新执行 `pnpm build:mp-weixin`，微信开发者工具运行的是 `dist/build/mp-weixin`。

后端对接重点：

- Django API 位于 `apps/api`。
- 组队模块在 `apps/api/teammates`。
- 登录模块在 `apps/api/accounts`。
- 本地 demo 微信登录只在 `DEBUG=1` 且未配置微信密钥时启用。
- 后续接入真实微信登录时，需要配置真实 `WECHAT_MINIAPP_APPID` 和 `WECHAT_MINIAPP_SECRET`。

产品/测试对接重点：

- 登录、发帖、组队发布均依赖本地后端运行。
- 组队发布需要登录和资料完善。
- 发布帖子和发布组队是两个独立功能。
- 如果界面显示旧内容，优先清理微信开发者工具编译缓存。

## 8. 当前建议的下一步

1. 接入真实微信 AppID 和 Secret，替换本地 demo 登录。
2. 给组队发布表单增加更明确的发布成功跳转或列表高亮。
3. 给发帖和组队发布增加端到端测试用例。
4. 真机调试时统一切换为局域网 IP 或线上 HTTPS API。
5. 根据实际产品需求补充图片上传、通知、私信等功能的完整验收清单。
