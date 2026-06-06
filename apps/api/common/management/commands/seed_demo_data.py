from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from chat.models import ChatMessage, ChatThread
from dating.models import DatingPreference, DatingProfile
from forum.models import ForumPost
from profiles.models import Profile
from teammates.models import TeamPost
from trade.models import TradePost


User = get_user_model()


DEMO_USERS = [
    {
        "email": "demo_frontend@campusclaw.local",
        "nickname": "前端小鹿",
        "full_name": "前端小鹿",
        "major": "软件工程",
        "grade": "2024",
        "interests": ["前端", "设计", "AI", "摄影"],
        "gender": "female",
        "height_cm": 166,
        "weight_kg": 52,
        "age": 20,
        "bio": "喜欢做有温度的校园产品，周末会拍照和看展。",
    },
    {
        "email": "demo_backend@campusclaw.local",
        "nickname": "后端阿川",
        "full_name": "后端阿川",
        "major": "计算机科学",
        "grade": "2023",
        "interests": ["后端", "算法", "篮球", "创业"],
        "gender": "male",
        "height_cm": 178,
        "weight_kg": 68,
        "age": 21,
        "bio": "后端和算法方向，正在找靠谱队友一起做比赛项目。",
    },
    {
        "email": "demo_product@campusclaw.local",
        "nickname": "产品七七",
        "full_name": "产品七七",
        "major": "数字媒体",
        "grade": "2025",
        "interests": ["产品", "运营", "文案", "电影"],
        "gender": "female",
        "height_cm": 162,
        "weight_kg": 48,
        "age": 19,
        "bio": "喜欢把混乱想法整理成清楚方案，也喜欢轻松聊天。",
    },
    {
        "email": "demo_trade@campusclaw.local",
        "nickname": "闲置星人",
        "full_name": "闲置星人",
        "major": "人工智能",
        "grade": "2022",
        "interests": ["AI", "阅读", "二手交易", "跑步"],
        "gender": "other",
        "height_cm": 170,
        "weight_kg": 60,
        "age": 22,
        "bio": "喜欢整理宿舍，也喜欢淘到刚刚好的二手好物。",
    },
]


CHAT_DEMO_USERS = [
    {
        "email": "demo_chat_design@campusclaw.local",
        "nickname": "设计阿梨",
        "full_name": "设计阿梨",
        "major": "视觉传达",
        "grade": "2024",
        "interests": ["UI", "插画", "摄影", "产品"],
        "gender": "female",
        "height_cm": 165,
        "weight_kg": 50,
        "age": 20,
        "bio": "喜欢把复杂功能变得更好理解，最近在练习小程序界面设计。",
    },
    {
        "email": "demo_chat_photo@campusclaw.local",
        "nickname": "摄影小周",
        "full_name": "摄影小周",
        "major": "新闻传播",
        "grade": "2023",
        "interests": ["摄影", "短视频", "活动", "Citywalk"],
        "gender": "male",
        "height_cm": 176,
        "weight_kg": 64,
        "age": 21,
        "bio": "校园活动摄影搭子，喜欢拍自然一点的人像和活动花絮。",
    },
    {
        "email": "demo_chat_math@campusclaw.local",
        "nickname": "数分小林",
        "full_name": "数分小林",
        "major": "统计学",
        "grade": "2022",
        "interests": ["数据分析", "数学建模", "Python", "咖啡"],
        "gender": "male",
        "height_cm": 174,
        "weight_kg": 63,
        "age": 22,
        "bio": "常年出没图书馆三楼，擅长把乱糟糟的数据整理成能讲清楚的图表。",
    },
    {
        "email": "demo_chat_keyboard@campusclaw.local",
        "nickname": "键盘学姐",
        "full_name": "键盘学姐",
        "major": "电子信息",
        "grade": "2021",
        "interests": ["数码", "键盘", "二手交易", "自习"],
        "gender": "female",
        "height_cm": 168,
        "weight_kg": 54,
        "age": 23,
        "bio": "喜欢折腾宿舍桌面，也愿意帮同学避坑二手数码。",
    },
    {
        "email": "demo_chat_runner@campusclaw.local",
        "nickname": "夜跑阿南",
        "full_name": "夜跑阿南",
        "major": "体育经济",
        "grade": "2024",
        "interests": ["跑步", "羽毛球", "社团", "夜宵"],
        "gender": "male",
        "height_cm": 181,
        "weight_kg": 72,
        "age": 20,
        "bio": "晚上操场固定刷圈，想找能互相监督的运动搭子。",
    },
    {
        "email": "demo_chat_music@campusclaw.local",
        "nickname": "音乐小夏",
        "full_name": "音乐小夏",
        "major": "音乐科技",
        "grade": "2025",
        "interests": ["音乐", "Live", "剪辑", "社团活动"],
        "gender": "female",
        "height_cm": 160,
        "weight_kg": 47,
        "age": 19,
        "bio": "喜欢 Live 和校园活动剪辑，聊天时经常顺手推荐歌单。",
    },
]


TEAM_POSTS = [
    {
        "author": "demo_backend@campusclaw.local",
        "title": "AI 校园助手比赛项目招前端和设计",
        "summary": "做一个能帮同学发帖、匹配和聊天的校园 AI 产品。",
        "details": "目前后端和基础功能已有雏形，希望找前端、UI 设计或产品同学一起完善演示和答辩。",
        "target_size": 4,
        "current_size": 1,
        "tags": ["AI", "校园产品", "比赛"],
        "required_skills": ["前端", "设计", "产品"],
        "is_highlighted": True,
        "bump_score": 6,
    },
    {
        "author": "demo_product@campusclaw.local",
        "title": "校园集市调研小组找数据分析同学",
        "summary": "一起做校园二手交易体验调研和可视化报告。",
        "details": "需要一位会问卷分析或可视化的同学，最终产出调研报告和展示海报。",
        "target_size": 3,
        "current_size": 1,
        "tags": ["交易", "调研", "数据分析"],
        "required_skills": ["运营", "文案", "算法"],
        "bump_score": 3,
    },
    {
        "author": "demo_frontend@campusclaw.local",
        "title": "周末校园摄影活动招搭子",
        "summary": "找 2 位同学一起拍 CampusClaw 宣传素材。",
        "details": "轻松拍摄校园角落、人物和小程序展示图，适合喜欢摄影或短视频的同学。",
        "target_size": 3,
        "current_size": 1,
        "tags": ["摄影", "活动", "宣传"],
        "required_skills": ["拍摄", "设计"],
        "bump_score": 2,
    },
]


TRADE_POSTS = [
    {
        "author": "demo_trade@campusclaw.local",
        "post_type": "sell",
        "title": "出一个几乎全新的蓝牙键盘",
        "description": "上学期买来写代码，用得不多，键帽干净，适合宿舍和图书馆。",
        "price": "89.00",
        "condition": "9成新",
        "tags": ["键盘", "数码", "学习"],
        "is_highlighted": True,
        "bump_score": 5,
    },
    {
        "author": "demo_frontend@campusclaw.local",
        "post_type": "sell",
        "title": "转让设计类书籍三本",
        "description": "包含排版、用户体验和配色相关书，适合做 UI 或产品入门。",
        "price": "45.00",
        "condition": "8成新",
        "tags": ["设计", "书籍", "产品"],
        "bump_score": 3,
    },
    {
        "author": "demo_backend@campusclaw.local",
        "post_type": "buy",
        "title": "求购二手显示器",
        "description": "希望 24 寸左右，能正常外接笔记本即可，预算 300 以内。",
        "price": "300.00",
        "condition": "功能正常",
        "tags": ["显示器", "数码", "求购"],
        "bump_score": 2,
    },
]


FORUM_POSTS = [
    {
        "author": "demo_product@campusclaw.local",
        "title": "比赛答辩怎么把产品故事讲清楚？",
        "body": "我发现答辩时不要一上来讲技术细节，先讲用户为什么需要它，再讲我们怎么解决，会更容易被听懂。",
        "category": "学习交流",
        "tags": ["比赛", "产品", "答辩"],
    },
    {
        "author": "demo_frontend@campusclaw.local",
        "title": "CampusClaw 首页视觉建议",
        "body": "橙色渐变很有活力，但按钮层级要更克制一点，让主要操作更突出。",
        "category": "项目合作",
        "tags": ["设计", "前端", "AI"],
    },
]


CHAT_THREADS = [
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_backend@campusclaw.local",
        "source_type": "team_post",
        "messages": [
            ("demo_backend@campusclaw.local", "嗨，我看到你对前端和设计都感兴趣，我们 AI 校园助手项目还缺一个能把页面打磨漂亮的人。"),
            ("demo_frontend@campusclaw.local", "可以呀，我比较熟 uni-app，也能顺手改一下交互细节。你们现在最缺哪一块？"),
            ("demo_backend@campusclaw.local", "主要是推荐卡片和答辩演示流程，如果你愿意，我们今晚可以先对一下分工。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_product@campusclaw.local",
        "source_type": "direct",
        "messages": [
            ("demo_product@campusclaw.local", "我整理了一版答辩故事线：先讲校园需求，再讲 AI 动作助手，最后展示推荐和聊天闭环。"),
            ("demo_frontend@campusclaw.local", "这个顺序很好，我可以配合把首页和 AI 弹层的演示路径再顺一下。"),
            ("demo_product@campusclaw.local", "那我们就用“推荐几个前端组队”和“推荐二手键盘”做两个亮点展示。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_design@campusclaw.local",
        "source_type": "contact_search",
        "messages": [
            ("demo_chat_design@campusclaw.local", "你好，我是阿梨，看到你在做 CampusClaw，感觉这个项目很适合做一点更有校园感的视觉。"),
            ("demo_frontend@campusclaw.local", "太好了！我们现在是橙色渐变风格，你觉得推荐卡片还可以怎么优化？"),
            ("demo_chat_design@campusclaw.local", "可以把推荐指数做得更像小徽章，按钮文案也更明确一点，比如联系发起人、填充申请。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_photo@campusclaw.local",
        "source_type": "team_post",
        "messages": [
            ("demo_chat_photo@campusclaw.local", "周末如果要拍小程序展示图，我可以带相机过去，顺便拍几张校园场景。"),
            ("demo_frontend@campusclaw.local", "好呀，我们需要几张论坛、匹配、聊天场景的宣传图，风格自然一点就行。"),
            ("demo_chat_photo@campusclaw.local", "没问题，到时候你把需要展示的页面提前准备好就行。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_math@campusclaw.local",
        "source_type": "team_post",
        "messages": [
            ("demo_chat_math@campusclaw.local", "我看到你们有校园集市调研，如果需要做问卷分析和可视化，我可以帮忙。"),
            ("demo_frontend@campusclaw.local", "太需要了！我们想把用户痛点、交易偏好和 AI 推荐效果讲得更直观一点。"),
            ("demo_chat_math@campusclaw.local", "可以，我建议先整理 3 个核心指标：发布转化、联系转化、推荐点击率，答辩时会很清楚。"),
            ("demo_frontend@campusclaw.local", "这个思路很稳，我晚点把现有演示流程发你，你帮我看下数据怎么包装。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_keyboard@campusclaw.local",
        "source_type": "trade_post",
        "messages": [
            ("demo_frontend@campusclaw.local", "你好，我看到你有蓝牙键盘相关的帖子，想问一下还能小刀吗？"),
            ("demo_chat_keyboard@campusclaw.local", "可以呀，如果今天在图书馆门口自提，80 就可以。键盘我会提前充好电。"),
            ("demo_frontend@campusclaw.local", "可以，那我晚上 7 点左右过去，你方便吗？"),
            ("demo_chat_keyboard@campusclaw.local", "方便，我到时候带上键盘和接收器，你可以现场试一下。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_runner@campusclaw.local",
        "source_type": "dating",
        "messages": [
            ("demo_chat_runner@campusclaw.local", "嗨，系统推荐说我们都喜欢运动和校园活动，就来打个招呼。"),
            ("demo_frontend@campusclaw.local", "你好呀，我平时跑得不多，不过很想找人一起慢慢恢复运动。"),
            ("demo_chat_runner@campusclaw.local", "可以从操场慢跑两圈开始，不卷速度，主要是坚持。跑完还能去吃夜宵。"),
            ("demo_frontend@campusclaw.local", "这个安排听起来很友好，下次你跑步前可以喊我一下。"),
        ],
    },
    {
        "user_a": "demo_frontend@campusclaw.local",
        "user_b": "demo_chat_music@campusclaw.local",
        "source_type": "direct",
        "messages": [
            ("demo_chat_music@campusclaw.local", "我听说 CampusClaw 想做比赛展示视频，如果需要背景音乐或剪辑节奏，我可以帮你们看看。"),
            ("demo_frontend@campusclaw.local", "太好了，我们现在有论坛、匹配、聊天和 AI 助手几个片段，想剪得轻快一点。"),
            ("demo_chat_music@campusclaw.local", "建议用 30 秒快节奏版本：前 5 秒讲痛点，中间展示 AI 推荐，最后收在聊天闭环。"),
            ("demo_frontend@campusclaw.local", "很像一个完整产品广告了，我喜欢这个结构。"),
        ],
    },
]


class Command(BaseCommand):
    help = "Seed CampusClaw demo users and content for recommendation demos."

    def handle(self, *args, **options):
        users = {}
        for item in [*DEMO_USERS, *CHAT_DEMO_USERS]:
            user, _ = User.objects.update_or_create(
                email=item["email"],
                defaults={
                    "nickname": item["nickname"],
                    "full_name": item["full_name"],
                    "is_active": True,
                    "is_email_verified": True,
                },
            )
            user.set_password("demo123456")
            user.save()
            profile, _ = Profile.objects.get_or_create(user=user)
            profile.headline = f"{item['major']} · {item['grade']} · {'、'.join(item['interests'][:2])}"
            profile.bio = item["bio"]
            profile.major = item["major"]
            profile.grade = item["grade"]
            profile.interests = item["interests"]
            profile.save()
            dating_profile, _ = DatingProfile.objects.get_or_create(user=user)
            dating_profile.nickname = item["nickname"]
            dating_profile.gender = item["gender"]
            dating_profile.height_cm = item["height_cm"]
            dating_profile.weight_kg = item["weight_kg"]
            dating_profile.age = item["age"]
            dating_profile.interests = item["interests"]
            dating_profile.bio = item["bio"]
            dating_profile.is_visible = True
            dating_profile.save()
            preference, _ = DatingPreference.objects.get_or_create(user=user)
            preference.preferred_genders = []
            preference.preferred_interests = item["interests"][:3]
            preference.min_age = 18
            preference.max_age = 25
            preference.min_height_cm = None
            preference.max_height_cm = None
            preference.min_weight_kg = None
            preference.max_weight_kg = None
            preference.preferred_personality_types = []
            preference.save()
            users[item["email"]] = user

        for item in TEAM_POSTS:
            TeamPost.objects.update_or_create(
                author=users[item["author"]],
                title=item["title"],
                defaults={key: value for key, value in item.items() if key not in {"author", "title"}},
            )

        for item in TRADE_POSTS:
            TradePost.objects.update_or_create(
                author=users[item["author"]],
                title=item["title"],
                defaults={key: value for key, value in item.items() if key not in {"author", "title"}},
            )

        for item in FORUM_POSTS:
            ForumPost.objects.update_or_create(
                author=users[item["author"]],
                title=item["title"],
                defaults={key: value for key, value in item.items() if key not in {"author", "title"}},
            )

        for item in CHAT_THREADS:
            first = users[item["user_a"]]
            second = users[item["user_b"]]
            user_a, user_b = (first, second) if str(first.id) < str(second.id) else (second, first)
            thread, _ = ChatThread.objects.get_or_create(
                user_a=user_a,
                user_b=user_b,
                defaults={"source_type": item["source_type"], "source_id": ""},
            )
            thread.source_type = item["source_type"]
            thread.source_id = ""
            thread.hidden_for_user_a = False
            thread.hidden_for_user_b = False
            thread.save(update_fields=["source_type", "source_id", "hidden_for_user_a", "hidden_for_user_b", "updated_at"])
            ChatMessage.objects.filter(thread=thread).delete()
            for sender_email, body in item["messages"]:
                ChatMessage.objects.create(
                    thread=thread,
                    sender=users[sender_email],
                    body=body,
                    is_read=sender_email == "demo_frontend@campusclaw.local",
                )

        self.stdout.write(self.style.SUCCESS("CampusClaw 演示数据已生成。演示账号统一密码：demo123456"))
