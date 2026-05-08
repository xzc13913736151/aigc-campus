import type { DatingCandidate, DatingMatch, DatingPreference, DatingProfile } from '../types/api'
import { request } from '../utils/request'

export function fetchDatingProfile() {
  return request<DatingProfile>('dating/profile/')
}

export function updateDatingProfile(payload: Omit<DatingProfile, 'id' | 'user' | 'updated_at'>) {
  return request<DatingProfile>('dating/profile/', {
    method: 'PUT',
    data: payload,
  })
}

export function fetchDatingPreference() {
  return request<DatingPreference>('dating/preferences/')
}

export function updateDatingPreference(payload: Omit<DatingPreference, 'id' | 'updated_at'>) {
  return request<DatingPreference>('dating/preferences/', {
    method: 'PUT',
    data: payload,
  })
}

export function fetchDatingCandidates() {
  return request<DatingCandidate[]>('dating/candidates/')
}

export function sendDatingSignal(payload: { target_user_id: string; signal: 'interested' | 'not_interested' }) {
  return request<{ matched: boolean; signal: 'interested' | 'not_interested' }>('dating/signals/', {
    method: 'POST',
    data: payload,
  })
}

export function fetchDatingMatches() {
  return request<DatingMatch[]>('dating/matches/')
}
