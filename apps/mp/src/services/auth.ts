import type { LoginResponse, UserSummary } from '../types/api'
import { request } from '../utils/request'

export function wechatLogin(code: string) {
  return request<LoginResponse>('auth/wechat-login/', {
    method: 'POST',
    auth: false,
    data: { code },
  })
}

export function fetchCurrentUser() {
  return request<UserSummary>('auth/me/')
}
