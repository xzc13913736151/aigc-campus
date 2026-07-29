export type UserSummary = {
  id: string
  claw_id: string
  email: string
  full_name: string
  nickname: string
  role: string
  is_email_verified: boolean
  email_verified_at: string | null
  created_at: string
  updated_at: string
}

export type ContactSearchUser = {
  id: string
  claw_id: string
  nickname: string
  full_name: string
  headline: string
  avatar_url: string
}

export type LoginResponse = {
  access: string
  refresh: string
  user?: UserSummary
}

export type ProfileResponse = {
  user: UserSummary
  nickname: string
  avatar_url: string
  headline: string
  bio: string
  gender: string
  major: string
  grade: string
  interests: string[]
}

export type TeamPost = {
  id: string
  title: string
  summary: string
  details: string
  tags: string[]
  required_skills: string[]
  target_size: number
  current_size: number
  status: 'open' | 'filled' | 'closed'
  is_highlighted: boolean
  bump_score: number
  bumped_at: string
  author: {
    id: string
    email: string
    nickname: string
    full_name: string
  }
  created_at?: string
  updated_at?: string
}

export type TeamApplication = {
  id: string
  post: TeamPost
  applicant: UserSummary
  message: string
  status: 'pending' | 'accepted' | 'rejected' | 'withdrawn'
  created_at: string
  updated_at: string
}

export type ForumComment = {
  id: string
  author: UserSummary
  parent: string | null
  body: string
  like_count: number
  is_liked: boolean
  replies: ForumComment[]
  created_at: string
}

export type ForumPost = {
  id: string
  author: UserSummary
  title: string
  summary: string
  body: string
  category: string
  tags: string[]
  is_deleted: boolean
  is_liked: boolean
  like_count: number
  comment_count: number
  comments: ForumComment[]
  image_urls: string[]
  created_at: string
  updated_at: string
}

export type NotificationItem = {
  id: string
  type:
    | 'forum_like'
    | 'forum_comment'
    | 'forum_reply'
    | 'team_application_created'
    | 'team_application_accepted'
    | 'team_application_rejected'
    | 'chat_message'
  title: string
  body: string
  target_type: string
  target_id: string
  extra: Record<string, unknown>
  is_read: boolean
  read_at: string | null
  actor: UserSummary | null
  created_at: string
  updated_at: string
}

export type ModerationReportTargetSnapshot = {
  exists: boolean
  label: string
  author_email?: string
  is_deleted?: boolean
  status?: string
  price?: string
  post_id?: string
}

export type ModerationReport = {
  id: string
  reporter: UserSummary
  target_type: string
  target_id: string
  target_snapshot: ModerationReportTargetSnapshot
  reason: string
  details: string
  status: 'open' | 'reviewing' | 'resolved' | 'rejected'
  created_at: string
  updated_at: string
}

export type ModerationReportStats = {
  all: number
  open: number
  reviewing: number
  resolved: number
  rejected: number
}

export type ModerationActionLog = {
  id: string
  actor: UserSummary | null
  report: string | null
  action: string
  target_type: string
  target_id: string | null
  note: string
  metadata: Record<string, unknown>
  created_at: string
}

export type BlockItem = {
  id: string
  reason: string
  created_at: string
  blocked_user_detail: UserSummary
}

export type DatingProfile = {
  id: string
  user: UserSummary
  nickname: string
  gender: 'unknown' | 'male' | 'female' | 'other'
  height_cm: number | null
  weight_kg: number | null
  age: number | null
  interests: string[]
  personality_type: string
  bio: string
  is_visible: boolean
  updated_at: string
}

export type DatingPreference = {
  id: string
  preferred_genders: Array<'unknown' | 'male' | 'female' | 'other'>
  min_height_cm: number | null
  max_height_cm: number | null
  min_weight_kg: number | null
  max_weight_kg: number | null
  min_age: number | null
  max_age: number | null
  preferred_interests: string[]
  preferred_personality_types: string[]
  updated_at: string
}

export type DatingCandidate = DatingProfile & {
  match_score: number
}

export type DatingMatch = {
  id: string
  counterpart: UserSummary | null
  created_at: string
}

export type ChatMessage = {
  id: string
  sender: UserSummary
  body: string
  image_url: string
  is_read: boolean
  read_at: string | null
  is_withdrawn: boolean
  withdrawn_at: string | null
  created_at: string
  updated_at: string
}

export type ChatThread = {
  id: string
  counterpart: UserSummary | null
  source_type: string
  source_id: string
  last_message: ChatMessage | null
  unread_count: number
  created_at: string
  updated_at: string
}

export type AssistantMessage = {
  id: string
  role: 'user' | 'assistant'
  body: string
  presentation?: AssistantPresentation
  created_at: string
  updated_at: string
}

export type AssistantPresentationField = {
  key: string
  label: string
  value: unknown
  display_value: string
  source: 'user' | 'context' | 'ai' | 'missing'
  required: boolean
  options?: Array<{ label: string; value: unknown }>
  custom_prompt?: string
  hint?: string
  confidence?: number
}

export type AssistantPresentation = {
  type: 'text' | 'clarification' | 'draft' | 'recommendations' | 'result'
  intent: string
  title: string
  fields: AssistantPresentationField[]
  missing_fields: string[]
  suggestions: string[]
}

export type AssistantActionProposal = {
  id: string
  kind:
    | 'forum_post_create'
    | 'forum_comment_create'
    | 'forum_post_like'
    | 'forum_comment_like'
    | 'team_post_create'
    | 'team_apply'
    | 'trade_post_create'
    | 'trade_favorite'
    | 'team_recommendations'
    | 'dating_recommendations'
    | 'trade_recommendations'
    | 'context_chat_message_send'
    | 'dating_profile_update'
    | 'dating_preference_update'
    | 'dating_signal'
    | 'chat_message_send'
    | 'chat_message_batch_send'
    | 'profile_update'
  title: string
  target_page: string
  preview: Record<string, unknown>
  payload: Record<string, unknown>
  fill_payload: Record<string, unknown>
  status: 'pending' | 'executed' | 'dismissed' | 'expired'
  expires_at: string
  created_at: string
  updated_at: string
}

export type AssistantSessionState = {
  flow?: 'idle' | 'collecting' | 'confirming' | 'ready'
  intent?: string
  draft_kind?: AssistantActionProposal['kind'] | ''
  draft_target_page?: string
  missing_fields?: string[]
  missing_field_labels?: string[]
  collected_payload?: Record<string, unknown>
  expanded_preview?: string
  last_question?: string
  recipient_options?: Array<{ id: string; label: string; claw_id: string }>
}

export type AssistantSession = {
  id: string
  title: string
  page_type: 'forum' | 'publish' | 'messages' | 'me' | 'general'
  context_path: string
  context_target_type: string
  context_target_id: string
  state: AssistantSessionState
  last_message: AssistantMessage | null
  created_at: string
  updated_at: string
}

export type AssistantReplyResponse = {
  user_message: AssistantMessage
  assistant_message: AssistantMessage
  session: AssistantSession
  actions: AssistantActionProposal[]
}

export type AssistantActionExecuteResponse = {
  action: AssistantActionProposal
  result: {
    target_page?: string
    message?: string
    [key: string]: unknown
  }
}
