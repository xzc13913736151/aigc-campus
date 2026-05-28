import type { AssistantActionProposal } from '../types/api'

const ASSISTANT_PENDING_DRAFT_KEY = 'assistant.pending-draft'

export type AssistantPendingDraft = {
  kind: AssistantActionProposal['kind']
  target_page: string
  fill_payload: Record<string, unknown>
  created_at: number
}

export function saveAssistantDraft(action: AssistantActionProposal) {
  const draft: AssistantPendingDraft = {
    kind: action.kind,
    target_page: action.target_page,
    fill_payload: action.fill_payload,
    created_at: Date.now(),
  }
  uni.setStorageSync(ASSISTANT_PENDING_DRAFT_KEY, JSON.stringify(draft))
}

export function consumeAssistantDraft(targetPage: string, acceptedKinds: AssistantActionProposal['kind'][] = []) {
  const raw = uni.getStorageSync(ASSISTANT_PENDING_DRAFT_KEY)
  if (typeof raw !== 'string' || !raw) {
    return null
  }
  try {
    const draft = JSON.parse(raw) as AssistantPendingDraft
    const expired = Date.now() - Number(draft.created_at || 0) > 30 * 60 * 1000
    const pageMismatch = draft.target_page && !draft.target_page.startsWith(targetPage)
    const kindMismatch = acceptedKinds.length > 0 && !acceptedKinds.includes(draft.kind)
    if (expired) {
      uni.removeStorageSync(ASSISTANT_PENDING_DRAFT_KEY)
      return null
    }
    if (pageMismatch || kindMismatch) {
      return null
    }
    uni.removeStorageSync(ASSISTANT_PENDING_DRAFT_KEY)
    return draft
  } catch {
    uni.removeStorageSync(ASSISTANT_PENDING_DRAFT_KEY)
    return null
  }
}
