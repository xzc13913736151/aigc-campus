from __future__ import annotations

import re
from typing import TypedDict


FORUM_CATEGORIES = (
    "校园日常",
    "学习交流",
    "活动组局",
    "实习求职",
    "项目合作",
    "组队招募",
    "情绪树洞",
)

FORUM_CATEGORY_GUIDANCE = {
    "校园日常": "食堂、宿舍、校园见闻和普通生活分享；只有存在明确校园生活内容时才选择，不能作为缺省分类。",
    "学习交流": "课程、作业、考试、学习方法、学业求助和升学备考。",
    "活动组局": "邀请他人参加运动、游戏、出游或聚会，通常包含活动、时间、地点或参与意图。",
    "实习求职": "实习、校招、简历、面试、职业选择和求职经验。",
    "项目合作": "项目想法、技术或产品讨论、开发经验和项目复盘，不包含明确招募成员的诉求。",
    "组队招募": "明确寻找成员、缺少某个角色、说明人数或招募队友。",
    "情绪树洞": "压力、焦虑、孤独、关系困扰、倾诉和情绪表达。",
}


class ForumCategoryDecision(TypedDict):
    category: str
    confidence: float
    reason: str
    alternatives: list[str]


_CATEGORY_SIGNALS = {
    "校园日常": ("食堂", "宿舍", "寝室", "校园", "校门", "快递站", "二手群", "校园卡", "选课体验"),
    "学习交流": ("学习", "复习", "高数", "考试", "自习", "图书馆", "课程", "作业", "考研", "四六级", "论文", "绩点"),
    "活动组局": ("羽毛球", "篮球", "足球", "乒乓球", "桌游", "唱歌", "电影", "看电影", "骑行", "跑步", "聚餐", "出游", "活动"),
    "实习求职": ("实习", "校招", "求职", "简历", "面试", "笔试", "offer", "内推", "职业规划", "暑期实习"),
    "项目合作": ("项目经验", "项目复盘", "开发经验", "技术方案", "产品想法", "开源", "需求分析", "小程序开发", "技术交流"),
    "组队招募": ("找队友", "招募", "招人", "组队", "队友", "缺一个", "还差", "目标人数", "找同学一起做"),
    "情绪树洞": ("压力很大", "焦虑", "孤独", "难过", "失恋", "崩溃", "迷茫", "想倾诉", "想说说", "心情不好", "关系困扰"),
}

_INVITATION_SIGNALS = ("约", "一起", "来人", "有人吗", "报名", "参加", "组局", "搭子")
_RECRUITMENT_ROLE_PATTERN = re.compile(r"(?:缺|需要|招|找)(?:一名|一个|位|个)?\s*(?:前端|后端|设计|产品|算法|运营|队友|成员)")
_TIME_PLACE_PATTERN = re.compile(r"(?:周[一二三四五六日天]|星期|今晚|明天|后天|上午|下午|晚上|\d{1,2}[点时]|操场|体育馆|球场|活动室)")


def explicit_forum_category(text: str) -> str:
    clean = str(text or "").strip()
    choice_match = re.search(
        rf"(?:分类)?(?:改成|改为|换成|选择|选|归到|归为|设为)\s*[“\"']?({'|'.join(FORUM_CATEGORIES)})",
        clean,
    )
    if choice_match:
        return choice_match.group(1)
    for category in FORUM_CATEGORIES:
        denied = re.search(rf"(?:不是|不要|别选|不属于)\s*[“\"']?{re.escape(category)}", clean)
        if category in clean and not denied:
            return category
    return ""


def looks_like_team_recruitment(text: str) -> bool:
    clean = str(text or "").strip()
    return bool(
        _RECRUITMENT_ROLE_PATTERN.search(clean)
        or any(signal in clean for signal in _CATEGORY_SIGNALS["组队招募"])
    )


def looks_like_activity_group(text: str) -> bool:
    """Identify social/leisure invitations that should be forum activities, not team recruitment."""
    clean = str(text or "").strip()
    has_activity = any(signal in clean for signal in _CATEGORY_SIGNALS["活动组局"])
    has_invitation = any(signal in clean for signal in _INVITATION_SIGNALS)
    return has_activity and (has_invitation or bool(_TIME_PLACE_PATTERN.search(clean)))


def classify_forum_category(text: str) -> ForumCategoryDecision:
    clean = str(text or "").strip()
    explicit = explicit_forum_category(clean)
    if explicit:
        return {
            "category": explicit,
            "confidence": 1.0,
            "reason": f"用户明确指定分类为“{explicit}”",
            "alternatives": [],
        }

    scores = {category: 0 for category in FORUM_CATEGORIES}
    evidence: dict[str, list[str]] = {category: [] for category in FORUM_CATEGORIES}
    for category, signals in _CATEGORY_SIGNALS.items():
        for signal in signals:
            if signal.lower() in clean.lower():
                scores[category] += 2
                evidence[category].append(signal)

    if looks_like_team_recruitment(clean):
        scores["组队招募"] += 5
        evidence["组队招募"].append("明确招募成员或角色")
        scores["项目合作"] = max(0, scores["项目合作"] - 2)

    activity_signal = bool(evidence["活动组局"])
    invitation_signal = any(signal in clean for signal in _INVITATION_SIGNALS)
    if activity_signal and invitation_signal:
        scores["活动组局"] += 4
        evidence["活动组局"].append("包含参与邀请")
    if activity_signal and _TIME_PLACE_PATTERN.search(clean):
        scores["活动组局"] += 2
        evidence["活动组局"].append("包含时间或地点")

    ranked = sorted(scores, key=lambda category: scores[category], reverse=True)
    winner = ranked[0]
    top_score = scores[winner]
    second_score = scores[ranked[1]]
    if top_score == 0:
        return {"category": "", "confidence": 0.0, "reason": "内容中没有足够的分类依据", "alternatives": []}

    margin = top_score - second_score
    confidence = 0.92 if top_score >= 7 and margin >= 3 else 0.82 if top_score >= 2 and margin >= 2 else 0.66
    matched = "、".join(list(dict.fromkeys(evidence[winner]))[:3])
    alternatives = [category for category in ranked[1:] if scores[category] > 0][:2]
    return {
        "category": winner,
        "confidence": confidence,
        "reason": f"内容包含{matched}" if matched else FORUM_CATEGORY_GUIDANCE[winner],
        "alternatives": alternatives,
    }
