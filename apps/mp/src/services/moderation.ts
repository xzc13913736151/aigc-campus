import type { BlockItem, ModerationActionLog, ModerationReport, ModerationReportStats } from '../types/api'
import { request } from '../utils/request'
import { buildQuery } from '../utils/query'

export function createModerationReport(payload: {
  target_type: 'user' | 'dating_profile' | 'team_post' | 'forum_post' | 'comment' | 'trade_post'
  target_id: string
  reason: string
  details?: string
}) {
  return request<{
    id: string
    target_type: string
    target_id: string
    reason: string
    details: string
    status: string
    created_at: string
  }>('moderation/reports/', {
    method: 'POST',
    data: payload,
  })
}

export function fetchMyBlocks() {
  return request<BlockItem[]>('moderation/blocks/')
}

export function createBlock(payload: { blocked_user: string; reason?: string }) {
  return request<{
    id: string
    reason: string
    created_at: string
  }>('moderation/blocks/', {
    method: 'POST',
    data: payload,
  })
}

export function deleteBlock(blockId: string) {
  return request<void>(`moderation/blocks/${blockId}/`, {
    method: 'DELETE',
  })
}

export function fetchModerationReportStats() {
  return request<ModerationReportStats>('moderation/admin/reports/stats/')
}

export function fetchModerationReports(params?: { status?: string; target_type?: string }) {
  const suffix = buildQuery({
    status: params?.status,
    target_type: params?.target_type,
  })
  return request<ModerationReport[]>(`moderation/admin/reports/${suffix}`)
}

export function reviewModerationReport(
  reportId: string,
  payload: { status: string; action?: 'none' | 'delete_forum_post' | 'delete_forum_comment' | 'close_trade_post' },
) {
  return request<{ status: string }>(`moderation/admin/reports/${reportId}/`, {
    method: 'PATCH',
    data: payload,
  })
}

export function fetchModerationActionLogs() {
  return request<ModerationActionLog[]>('moderation/admin/action-logs/')
}
