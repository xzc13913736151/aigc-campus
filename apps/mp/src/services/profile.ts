import type { ProfileResponse } from '../types/api'
import { uploadFile } from '../utils/upload'
import { request } from '../utils/request'

export type UpdateMyProfilePayload = Pick<
  ProfileResponse,
  'nickname' | 'avatar_url' | 'headline' | 'bio' | 'gender' | 'major' | 'grade' | 'interests'
>

export function fetchMyProfile() {
  return request<ProfileResponse>('profile/me/')
}

export function updateMyProfile(payload: UpdateMyProfilePayload) {
  return request<ProfileResponse>('profile/me/', {
    method: 'PUT',
    data: payload,
  })
}

export function uploadMyAvatar(filePath: string) {
  return uploadFile<ProfileResponse>('profile/me/avatar/', filePath)
}
