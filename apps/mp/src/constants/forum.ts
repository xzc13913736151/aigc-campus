export const FORUM_CATEGORIES = [
  '校园日常',
  '学习交流',
  '活动组局',
  '实习求职',
  '项目合作',
  '组队招募',
  '情绪树洞',
] as const

export type ForumCategory = (typeof FORUM_CATEGORIES)[number]
