# CampusClaw 前端接口文档

> 版本：2026-07-23。本文件以 apps/api 的 Django 路由、视图、序列化器，以及 apps/mp/src/services 的实际调用为准，供前端重构和联调使用。展示名为 CampusClaw；后端局部内部类名仍保留 PairUp 历史命名，不影响接口。

## 1. 通用约定

| 项目 | 约定 |
| --- | --- |
| 本地 API 基址 | http://127.0.0.1:8000/api/v1 |
| 真机 API 基址 | http://电脑IPv4:8000/api/v1 |
| JSON 请求 | Content-Type: application/json |
| 身份认证 | Authorization: Bearer 访问令牌 |
| ID / 时间 | UUID 字符串 / ISO 8601 时间字符串 |
| 列表响应 | 直接为 JSON 数组；目前没有 results/count/next 分页包装 |
| 可匿名读取 | 论坛、组队、交易的列表和详情；其余接口需要登录 |

除上传外，请求体均为 JSON。所有 API 路径应保留结尾的 /。访问令牌有效 30 分钟，刷新令牌有效 7 天；小程序现有封装遇到 401 时会刷新令牌并重试一次，刷新失败后跳转登录。

| 状态码 | 说明 | 常见响应 |
| --- | --- | --- |
| 200 | 查询、更新、动作成功 | 资源对象或结果对象 |
| 201 | 创建成功 | 新资源对象 |
| 202 | 验证码请求已接受 | { detail, email, expires_in } |
| 204 | 删除或退出成功 | 空响应体 |
| 400 | 字段校验或业务条件不满足 | { detail } 或 { 字段: [错误] } |
| 401 | 缺少、过期或无效令牌 | { detail } |
| 403 | 已登录但无资源权限或管理权限 | { detail } |
| 404 | 资源不存在，或私有资源对当前用户不可见 | { detail } |

前端应优先显示字符串 detail；字段错误应逐字段展示，不能假定错误信息总是中文。

### 1.1 公共对象与枚举

UserSummary 字段：id、claw_id、email、full_name、nickname、role、is_email_verified、email_verified_at、created_at、updated_at。role 可取 user 或 admin；email_verified_at 可为 null，文本字段可能为空字符串。

业务对象的 author、applicant、sender、actor、counterpart 等字段均复用 UserSummary；通知的 actor 可为 null。

| 字段 | 可用值 |
| --- | --- |
| gender | unknown、male、female、other |
| 组队帖 status | open、filled、closed |
| 组队申请 status | pending、accepted、rejected、withdrawn |
| 交易 post_type | sell、buy、exchange、service |
| 交易 status | open、reserved、completed、closed |
| 交友 signal | interested、not_interested |
| 举报 target_type | user、dating_profile、team_post、forum_post、comment、trade_post |
| 举报 status | open、reviewing、resolved、rejected |

## 2. 系统与认证

| 方法 | 路径 | 登录 | 请求/说明 | 成功响应 |
| --- | --- | --- | --- | --- |
| GET | /health/ | 否 | 根路由，不带 API 前缀 | { status: ok } |
| GET | /api/schema/ | 否 | 根路由 OpenAPI schema | schema |
| GET | /api/docs/ | 否 | 根路由 Swagger UI | HTML |
| GET | /api/redoc/ | 否 | 根路由 Redoc | HTML |
| POST | /auth/email-code/request/ | 否 | { email } | 202，{ detail, email, expires_in } |
| POST | /auth/register/ | 否 | email、password、verification_code、full_name?、nickname? | 201，UserSummary |
| POST | /auth/login/ | 否 | { email, password } | LoginResponse |
| POST | /auth/wechat-login/ | 否 | { code } | LoginResponse |
| POST | /auth/refresh/ | 否 | { refresh } | { access, refresh? } |
| POST | /auth/logout/ | 是 | { refresh? } | 204 |
| GET | /auth/me/ | 是 | — | UserSummary |
| GET | /auth/contacts/search/?q=关键词 | 是 | 关键词至少 2 个字符 | ContactSearchUser[] |

LoginResponse 包含 access、refresh、user: UserSummary。注册密码最少 8 个字符，验证码为 6 位；验证码接口会拒绝已注册邮箱并受服务端重发冷却时间限制。微信登录依赖服务端微信小程序配置，未配置或 code 无效会返回 400。

联系人搜索按 claw_id 精确匹配，或按昵称/姓名模糊匹配，最多返回 20 条。每项字段为 id、claw_id、nickname、full_name、headline、avatar_url。

## 3. 用户资料

| 方法 | 路径 | 请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /profile/me/ | — | Profile |
| PUT / PATCH | /profile/me/ | 可更新字段 | Profile |
| POST | /profile/me/avatar/ | multipart，文件字段 file | Profile |
| GET | /profile/users/{user_id}/ | — | Profile |

Profile 字段：id、user: UserSummary、nickname、avatar_url、headline、bio、gender、major、grade、interests: string[]、updated_at。nickname 会同步更新 user.nickname；headline 最多 120 字符。

头像仅允许 JPG/JPEG/PNG/WEBP/GIF，最大 3 MB。现有小程序使用 PUT 提交完整资料，后端同时支持 PATCH 做局部更新。

## 4. AI 助手

AI 流程为 会话 → 消息 → 待确认动作。发送消息会同步调用模型，小程序为此接口设置了 180 秒超时；生成动作不等于已执行，必须经用户确认。

| 方法 | 路径 | 请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /assistant/sessions/ | — | AssistantSession[] |
| POST | /assistant/sessions/ | 会话字段 | 201，AssistantSession |
| GET | /assistant/sessions/{session_id}/messages/ | — | AssistantMessage[] |
| POST | /assistant/sessions/{session_id}/messages/ | { body } | 201，AssistantReply |
| GET | /assistant/sessions/{session_id}/actions/ | — | AssistantActionProposal[] |
| POST | /assistant/actions/{action_id}/execute/ | — | AssistantActionExecuteResponse |

创建会话字段：page_type、title?、context_path?、context_target_type?、context_target_id?。page_type 可取 forum、publish、messages、me、general；未传 title 时后端生成默认标题。

AssistantSession 字段：id、title、page_type、context_path、context_target_type、context_target_id、state、last_message、created_at、updated_at。last_message 可以为 null；state 是动态 JSON，目前可能有 flow、intent、draft_kind、missing_fields、collected_payload 等键，前端必须容错读取。

AssistantMessage 字段：id、role（user 或 assistant）、body、created_at、updated_at。

发送消息的成功结果含 user_message、assistant_message、session、actions。AssistantActionProposal 字段：id、kind、title、target_page、preview、payload、fill_payload、status、expires_at、created_at、updated_at。status 为 pending、executed、dismissed、expired；待执行动作默认两小时有效，同会话发送新消息会使旧待执行动作置为 dismissed。

动作可涉及论坛、组队、交易、交友、聊天、个人资料和推荐。前端应只用 title、preview、target_page 展示确认卡；不能假设 payload 的固定形状，也不能直接执行。确认后调用 execute，返回 action 和 result；result 通常包含 target_page、message 等动态字段。

## 5. 组队

| 方法 | 路径 | 登录 | 查询/请求体 | 成功响应 |
| --- | --- | --- | --- | --- |
| GET | /teammates/posts/ | 否 | q、tag、status 可选 | TeamPost[] |
| POST | /teammates/posts/ | 是 | 组队帖字段 | 201，TeamPost |
| GET | /teammates/posts/mine/ | 是 | — | TeamPost[] |
| GET | /teammates/posts/{id}/ | 否 | — | TeamPost |
| PUT / PATCH | /teammates/posts/{id}/ | 仅作者 | 可编辑字段 | TeamPost |
| DELETE | /teammates/posts/{id}/ | 仅作者 | — | 204 |
| POST | /teammates/posts/{post_id}/apply/ | 是 | { message } | 201，TeamApplication |
| GET | /teammates/applications/mine/ | 是 | — | TeamApplication[] |
| GET | /teammates/applications/received/ | 是 | — | TeamApplication[] |
| PATCH | /teammates/applications/{id}/review/ | 帖子作者 | { status: accepted 或 rejected } | TeamApplication |

TeamPost 请求字段：title、summary、details、target_size、required_skills: string[]、tags: string[]、status?。title 最多 120 字，summary 最多 200 字，target_size 必须为 2–20。

TeamPost 响应字段：id、author、title、summary、details、target_size、current_size、required_skills、tags、status、is_highlighted、bump_score、bumped_at、created_at、updated_at。其中 current_size、作者、置顶和热度字段只读。

TeamApplication 字段：id、post: TeamPost、applicant: UserSummary、message、status、created_at、updated_at。不得申请自己的帖子或重复申请。接受申请后后端增加 current_size，达到目标人数自动把帖子改为 filled。

## 6. 论坛

| 方法 | 路径 | 登录 | 查询/请求体 | 成功响应 |
| --- | --- | --- | --- | --- |
| GET | /forum/posts/ | 否 | q、category 可选 | ForumPost[] |
| POST | /forum/posts/ | 是 | { title, body, category?, tags? } | 201，ForumPost |
| GET | /forum/posts/mine/ | 是 | — | ForumPost[] |
| GET | /forum/posts/{id}/ | 否 | — | ForumPost |
| PUT / PATCH | /forum/posts/{id}/ | 仅作者 | title、body、category、tags | ForumPost |
| DELETE | /forum/posts/{id}/ | 仅作者 | — | 204，软删除 |
| GET | /forum/posts/{post_id}/comments/ | 否 | — | 顶层 ForumComment[] |
| POST | /forum/posts/{post_id}/comments/ | 是 | { body, parent?: uuid 或 null } | 201，ForumComment |
| POST | /forum/posts/{post_id}/like/ | 是 | — | { liked, like_count } |
| POST | /forum/comments/{comment_id}/like/ | 是 | — | { liked, like_count } |
| POST | /forum/comment-likes/{comment_id}/ | 是 | — | 同上，兼容别名 |
| POST | /forum/posts/{post_id}/images/ | 仅帖子作者 | multipart，文件字段 image | 201，图片对象 |

ForumPost 字段：id、author、title、summary、body、category、tags、is_deleted、is_liked、like_count、comment_count、comments、image_urls、created_at、updated_at。summary 由后端从 body 截取最多 120 字；comments 是含 replies 的完整顶层评论树；image_urls 为绝对 URL 数组。

ForumComment 字段：id、author、parent、body、like_count、is_liked、replies、created_at。parent 必须属于同一帖子。点赞是切换语义，重复请求会取消点赞。帖子删除是软删除，公开列表和详情不再返回；我的帖子接口仍可能返回其删除标记。论坛图片允许 JPG/JPEG/PNG/WEBP/GIF，最大 5 MB。

## 7. 交友匹配

| 方法 | 路径 | 请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /dating/profile/ | — | DatingProfile |
| PUT / PATCH | /dating/profile/ | 资料字段 | DatingProfile |
| GET | /dating/preferences/ | — | DatingPreference |
| PUT / PATCH | /dating/preferences/ | 偏好字段 | DatingPreference |
| GET | /dating/candidates/ | — | DatingCandidate[] |
| POST | /dating/signals/ | { target_user_id, signal } | { matched, signal } |
| GET | /dating/matches/ | — | DatingMatch[] |

均要求登录。首次读取资料或偏好时，后端会自动创建空对象。

DatingProfile 字段：id、user、nickname、gender、height_cm、weight_kg、age、interests、personality_type、bio、is_visible、updated_at；身高、体重、年龄可为 null，interests 为字符串数组。

DatingPreference 字段：id、preferred_genders、min_height_cm、max_height_cm、min_weight_kg、max_weight_kg、min_age、max_age、preferred_interests、preferred_personality_types、updated_at；数值上下限可为 null。

DatingCandidate 等同 DatingProfile，额外有 0–100 的 match_score，按分数降序。双方都发 interested 才返回 matched=true 并生成匹配；同一目标的新信号覆盖旧信号。禁止给自己或互相屏蔽的用户发信号。DatingMatch 字段为 id、counterpart、created_at。

## 8. 私聊

### 8.1 HTTP 接口

| 方法 | 路径 | 请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /chat/threads/ | — | ChatThread[] |
| POST | /chat/threads/ | { target_user_id, source_type?, source_id? } | 201，ChatThread |
| GET | /chat/threads/{thread_id}/messages/ | — | { thread, messages } |
| POST | /chat/threads/{thread_id}/messages/ | { body } | 201，ChatMessage |
| POST | /chat/threads/{thread_id}/images/ | multipart，文件字段 image | 201，ChatMessage |
| POST | /chat/threads/{thread_id}/mark-read/ | { mark_read: true } | { detail } |
| POST | /chat/threads/{thread_id}/messages/{message_id}/withdraw/ | { withdraw: true } | ChatMessage |
| POST | /chat/threads/{thread_id}/hide/ | — | { detail } |

均要求登录，且只有会话参与者可访问。会话以两位用户为唯一组合，重复创建会返回同一会话并恢复本人隐藏状态。

ChatThread 字段：id、counterpart、source_type、source_id、last_message、unread_count、created_at、updated_at。

ChatMessage 字段：id、sender、body、image_url、is_read、read_at、is_withdrawn、withdrawn_at、created_at、updated_at。读取消息列表会自动把对方未读消息设为已读。撤回仅允许本人消息，后端把 body 改为 This message was withdrawn.；隐藏仅影响当前用户，任意新消息都会重新显示会话。

### 8.2 WebSocket

将 HTTP 基址的 http(s)://主机/api/v1 改为 ws(s)://主机，连接时增加查询参数 token=访问令牌：

    ws://127.0.0.1:8000/ws/chat/{thread_id}/?token=访问令牌
    ws://127.0.0.1:8000/ws/chat/inbox/?token=访问令牌
    ws://127.0.0.1:8000/ws/notifications/?token=访问令牌

聊天连接成功先收到 { type: chat.ready, thread_id }；收件箱连接收到 { type: chat.inbox.ready }。无效令牌、非参与者或被屏蔽时服务端直接关闭连接。

聊天会话可发送三种 JSON：{ type: message.send, body }、{ type: typing.start }、{ type: typing.stop }。

| 服务端 type | 主要字段 | 用途 |
| --- | --- | --- |
| chat.message | thread_id、message: ChatMessage | 新文本、图片或撤回后的消息 |
| chat.read | thread_id、message_ids、read_at | 批量已读 |
| chat.presence | thread_id、user_id、online | 上下线 |
| chat.typing | thread_id、user_id、is_typing | 输入状态 |
| chat.thread | thread: ChatThread | 收件箱会话快照更新 |
| chat.thread_state | thread_id、user_id、online?、is_typing? | 收件箱在线/输入状态 |
| chat.error | message | 空消息或不支持动作 |

HTTP 发送与 WebSocket message.send 都会创建真实消息；同一条消息只能选一种通道，避免重复。

## 9. 通知

| 方法 | 路径 | 查询/请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /notifications/ | unread=1，也接受 true 或 yes | Notification[] |
| PATCH | /notifications/{id}/ | { is_read: true } | Notification |
| GET | /notifications/unread-count/ | — | { unread_count } |
| POST | /notifications/mark-all-read/ | — | { detail } |

均要求登录。Notification 字段：id、type、title、body、target_type、target_id、extra、is_read、read_at、actor、created_at、updated_at。extra 是跳转上下文；聊天通知含 thread_id、message_id，论坛通知含 post_id 和可选 comment_id。

通知 WebSocket 使用上一节地址；服务端直接推送一个 Notification 对象，不额外包裹 type。应读取对象自身 type，取值为 forum_like、forum_comment、forum_reply、team_application_created、team_application_accepted、team_application_rejected、chat_message。

## 10. 校园交易

| 方法 | 路径 | 登录 | 查询/请求体 | 成功响应 |
| --- | --- | --- | --- | --- |
| GET | /trade/posts/ | 否 | q、type、tag 可选 | TradePost[] |
| POST | /trade/posts/ | 是 | 创建字段 | 201，TradePost |
| GET | /trade/posts/mine/ | 是 | — | TradePost[] |
| GET | /trade/posts/{id}/ | 否 | — | TradePost，同时浏览数加一 |
| PUT / PATCH | /trade/posts/{id}/ | 仅作者 | 可编辑字段 | TradePost |
| DELETE | /trade/posts/{id}/ | 仅作者 | — | 204 |
| POST | /trade/posts/{post_id}/favorite/ | 是 | — | 201，TradeFavorite |
| DELETE | /trade/posts/{post_id}/favorite/ | 是 | — | 204 |
| GET | /trade/matches/ | 是 | — | TradeMatch[] |

创建字段：post_type、title、description、price?、is_negotiable?、condition?、tags?、image_urls?。price 可为 null，但不可为负。

TradePost 字段：id、author、post_type、title、description、price、is_negotiable、condition、tags、image_urls、status、view_count、is_highlighted、bump_score、is_favorited、created_at、updated_at。仅传 status 更新时后端使用状态专用校验；其他更新应避免回传作者、浏览数、置顶、热度等只读字段。

公开列表只返回 open 状态，排序是置顶、热度、创建时间；我的帖子接口返回本人全部状态。不能收藏自己的帖子，重复 POST 收藏为幂等。TradeFavorite 为 id、post、created_at；TradeMatch 为 id、counterparty、match_type（favorite、chat、reservation）、related_post、created_at。

## 11. 举报、屏蔽与管理端

### 11.1 普通用户

| 方法 | 路径 | 请求体 | 成功响应 |
| --- | --- | --- | --- |
| POST | /moderation/reports/ | { target_type, target_id, reason, details? } | 201，Report |
| GET | /moderation/blocks/ | — | Block[] |
| POST | /moderation/blocks/ | { blocked_user, reason? } | 201，Block |
| DELETE | /moderation/blocks/{id}/ | — | 204 |

均要求登录。reason 最多 160 字。Report 字段：id、reporter、target_type、target_id、reason、details、status、created_at，初始 status 为 open。

Block 字段：id、user、blocked_user_detail、reason、created_at。请求字段必须叫 blocked_user，不能屏蔽自己；重复屏蔽会触发唯一约束错误。屏蔽会影响联系人搜索、交友候选、聊天、通知和双方互动。

### 11.2 管理员

下列接口需要 role=admin 或 Django is_staff=true；普通用户应处理 403。

| 方法 | 路径 | 查询/请求体 | 成功响应 |
| --- | --- | --- | --- |
| GET | /moderation/admin/reports/stats/ | — | { all, open, reviewing, resolved, rejected } |
| GET | /moderation/admin/reports/ | status、target_type 可选 | AdminReport[] |
| GET | /moderation/admin/reports/{id}/ | — | AdminReport |
| PATCH | /moderation/admin/reports/{id}/ | { status, action? } | { status } |
| GET | /moderation/admin/action-logs/ | — | ModerationActionLog[]，最多 30 条 |

AdminReport 在 Report 基础上增加 target_snapshot、updated_at。target_snapshot 仅供审核展示，可能为 { exists: false, label }，不能当作目标详情的权威来源。

| action | 适用 target_type | 效果 |
| --- | --- | --- |
| none，默认 | 任意 | 仅更新举报状态 |
| delete_forum_post | forum_post | 软删除论坛帖 |
| delete_forum_comment | comment | 删除评论 |
| close_trade_post | trade_post | 将交易帖改为 closed |

每次审核都会写入日志。ModerationActionLog 字段：id、actor、report、action、target_type、target_id、note、metadata、created_at。

## 12. 上传与前端优化注意事项

| 场景 | 路径 | 文件字段 | 限制 |
| --- | --- | --- | --- |
| 头像 | /profile/me/avatar/ | file | 图片白名单，最大 3 MB |
| 论坛配图 | /forum/posts/{post_id}/images/ | image | 图片白名单，最大 5 MB，仅作者 |
| 聊天图片 | /chat/threads/{thread_id}/images/ | image | 图片白名单，最大 5 MB，仅参与者 |

允许 JPG、JPEG、PNG、WEBP、GIF。浏览器上传应带 Bearer token，且不要手工设置 multipart Content-Type，让浏览器生成 boundary。

- 列表尚未支持服务端分页；可先做虚拟列表，但不要假定 page 或 limit 参数已经生效。
- is_liked、is_favorited、unread_count 都是当前登录用户视角；匿名访问时布尔值为 false。
- 论坛详情已经内嵌评论树，打开详情后不必无条件再请求评论列表。
- 私聊消息 GET 有自动已读副作用；实时更新应优先 WebSocket，断线后回退 HTTP。
- UI 隐藏作者/管理员按钮不能替代 403 处理；私有资源也可能返回 404。
- AI payload 为动态 JSON，必须白名单展示、用户确认、可失败重试，不能直接当作任意请求执行。
- 常规请求当前超时 15 秒，AI 消息为 180 秒；前端应区分网络错误和业务 400。

## 13. 推荐联调顺序

1. GET /health/ 确认后端可达。
2. 登录取得 access/refresh，再 GET /api/v1/auth/me/ 验证 Authorization Header。
3. 先接论坛、组队、交易读取，再接创建、点赞、收藏等写入。
4. 最后接聊天和通知 WebSocket。
5. 真机和手机浏览器不能使用 127.0.0.1，必须换成电脑局域网 IPv4。

本地展示数据可通过 python apps/api/manage.py seed_demo_data 创建；账号密码见项目 README。本文不记录环境变量或第三方密钥。
