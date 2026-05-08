import type { TeamApplication, TeamPost } from '../types/api'
import { request } from '../utils/request'

export function fetchTeammatePosts(query = '') {
  const suffix = query ? `?q=${encodeURIComponent(query)}` : ''
  return request<TeamPost[]>(`teammates/posts/${suffix}`, {
    auth: false,
  })
}

export function createTeammatePost(payload: {
  title: string
  summary: string
  details: string
  target_size: number
  tags: string[]
  required_skills?: string[]
}) {
  return request<TeamPost>('teammates/posts/', {
    method: 'POST',
    data: payload,
  })
}

export function fetchMyTeammatePosts() {
  return request<TeamPost[]>('teammates/posts/mine/')
}

export function applyToTeammatePost(postId: string, payload: { message: string }) {
  return request<TeamApplication>(`teammates/posts/${postId}/apply/`, {
    method: 'POST',
    data: payload,
  })
}

export function fetchMyTeammateApplications() {
  return request<TeamApplication[]>('teammates/applications/mine/')
}

export function fetchReceivedTeammateApplications() {
  return request<TeamApplication[]>('teammates/applications/received/')
}

export function reviewTeammateApplication(
  applicationId: string,
  payload: { status: 'accepted' | 'rejected' },
) {
  return request<TeamApplication>(`teammates/applications/${applicationId}/review/`, {
    method: 'PATCH',
    data: payload,
  })
}
