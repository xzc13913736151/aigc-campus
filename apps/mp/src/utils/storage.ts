import { ACCESS_TOKEN_KEY, CURRENT_USER_KEY, LOGIN_REDIRECT_KEY, PROFILE_ONBOARDED_KEY, REFRESH_TOKEN_KEY } from '../constants'
import type { UserSummary } from '../types/api'

export function saveAuthTokens(access: string, refresh: string) {
  uni.setStorageSync(ACCESS_TOKEN_KEY, access)
  uni.setStorageSync(REFRESH_TOKEN_KEY, refresh)
}

export function saveAccessToken(access: string) {
  uni.setStorageSync(ACCESS_TOKEN_KEY, access)
}

export function clearAuthTokens() {
  uni.removeStorageSync(ACCESS_TOKEN_KEY)
  uni.removeStorageSync(REFRESH_TOKEN_KEY)
}

export function getAccessToken() {
  const token = uni.getStorageSync(ACCESS_TOKEN_KEY)
  return typeof token === 'string' && token ? token : null
}

export function getRefreshToken() {
  const token = uni.getStorageSync(REFRESH_TOKEN_KEY)
  return typeof token === 'string' && token ? token : null
}

export function saveCurrentUser(user: UserSummary) {
  uni.setStorageSync(CURRENT_USER_KEY, JSON.stringify(user))
}

export function getCurrentUser() {
  const raw = uni.getStorageSync(CURRENT_USER_KEY)
  if (typeof raw !== 'string' || !raw) {
    return null
  }

  try {
    return JSON.parse(raw) as UserSummary
  } catch {
    uni.removeStorageSync(CURRENT_USER_KEY)
    return null
  }
}

export function clearCurrentUser() {
  uni.removeStorageSync(CURRENT_USER_KEY)
}

export function saveLoginRedirect(url: string) {
  uni.setStorageSync(LOGIN_REDIRECT_KEY, url)
}

export function getLoginRedirect() {
  const url = uni.getStorageSync(LOGIN_REDIRECT_KEY)
  return typeof url === 'string' && url ? url : null
}

export function clearLoginRedirect() {
  uni.removeStorageSync(LOGIN_REDIRECT_KEY)
}

export function saveProfileOnboarded(value: boolean) {
  uni.setStorageSync(PROFILE_ONBOARDED_KEY, value ? '1' : '0')
}

export function getProfileOnboarded() {
  return uni.getStorageSync(PROFILE_ONBOARDED_KEY) === '1'
}

export function clearProfileOnboarded() {
  uni.removeStorageSync(PROFILE_ONBOARDED_KEY)
}
