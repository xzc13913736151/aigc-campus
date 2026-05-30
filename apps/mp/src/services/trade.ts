import type { UserSummary } from '../types/api'
import { request } from '../utils/request'
import { buildQuery } from '../utils/query'

export type TradePost = {
  id: string
  author: UserSummary
  post_type: 'sell' | 'buy' | 'exchange' | 'service'
  title: string
  description: string
  price: number | null
  is_negotiable: boolean
  condition: string
  tags: string[]
  image_urls: string[]
  status: 'open' | 'reserved' | 'completed' | 'closed'
  view_count: number
  is_highlighted: boolean
  bump_score: number
  is_favorited: boolean
  created_at: string
  updated_at: string
}

export type TradeMatch = {
  id: string
  counterparty: UserSummary | null
  match_type: 'favorite' | 'chat' | 'reservation'
  related_post: TradePost | null
  created_at: string
}

export function fetchTradePosts(params?: { q?: string; type?: string; tag?: string }) {
  return request<TradePost[]>(`trade/posts/${buildQuery({ q: params?.q, type: params?.type, tag: params?.tag })}`)
}

export function fetchMyTradePosts() {
  return request<TradePost[]>('trade/posts/mine/')
}

export function fetchTradePost(id: string) {
  return request<TradePost>(`trade/posts/${id}/`)
}

export function createTradePost(payload: {
  post_type: TradePost['post_type']
  title: string
  description: string
  price?: number | null
  is_negotiable?: boolean
  condition?: string
  tags?: string[]
  image_urls?: string[]
}) {
  return request<TradePost>('trade/posts/', {
    method: 'POST',
    data: payload,
  })
}

export function updateTradePost(id: string, payload: Partial<TradePost>) {
  return request<TradePost>(`trade/posts/${id}/`, {
    method: 'PATCH',
    data: payload,
  })
}

export function updateTradePostStatus(id: string, status: TradePost['status']) {
  return updateTradePost(id, { status })
}

export function deleteTradePost(id: string) {
  return request<void>(`trade/posts/${id}/`, {
    method: 'DELETE',
  })
}

export function favoriteTradePost(postId: string) {
  return request<void>(`trade/posts/${postId}/favorite/`, {
    method: 'POST',
  })
}

export function unfavoriteTradePost(postId: string) {
  return request<void>(`trade/posts/${postId}/favorite/`, {
    method: 'DELETE',
  })
}

export function fetchMyTradeMatches() {
  return request<TradeMatch[]>('trade/matches/')
}
