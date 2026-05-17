import { computed, ref } from 'vue'

import { BASE_URL } from '../constants'
import type { LoginResponse, ProfileResponse, UserSummary } from '../types/api'
import { buildQuery } from './query'
import {
  clearAuthTokens,
  clearCurrentUser,
  clearLoginRedirect,
  clearProfileOnboarded,
  getAccessToken,
  getCurrentUser,
  getLoginRedirect,
  getProfileOnboarded,
  getRefreshToken,
  saveAccessToken,
  saveAuthTokens,
  saveCurrentUser,
  saveLoginRedirect,
  saveProfileOnboarded,
} from './storage'

const LOGIN_PAGE_URL = '/pages/auth/login'
const DEFAULT_AUTHED_URL = '/pages/forum/index'
const PROFILE_PAGE_URL = '/pages/profile/index'
const LEGACY_REDIRECTS: Record<string, string> = {
  '/pages/home/index': DEFAULT_AUTHED_URL,
  '/pages/dashboard/index': DEFAULT_AUTHED_URL,
}
const TAB_PAGES = new Set([
  '/pages/forum/index',
  '/pages/publish/index',
  '/pages/messages/index',
  '/pages/me/index',
])

export const currentUser = ref<UserSummary | null>(getCurrentUser())
export const authReady = ref(false)
export const profileOnboarded = ref(getProfileOnboarded())
export const accessToken = ref<string | null>(getAccessToken())
export const isAuthenticated = computed(() => Boolean(accessToken.value))

let bootstrapPromise: Promise<void> | null = null
let refreshPromise: Promise<string | null> | null = null

type RawRequestOptions = {
  method?: 'GET' | 'POST'
  token?: string | null
  data?: Record<string, unknown>
}

function encodeQuery(params: Record<string, unknown>) {
  return buildQuery(params)
}

function getCurrentPageUrl() {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1] as
    | {
        route?: string
        options?: Record<string, unknown>
      }
    | undefined

  if (!current?.route) {
    return ''
  }

  return `/${current.route}${encodeQuery(current.options ?? {})}`
}

function getPathname(url: string) {
  return url.split('?')[0]
}

function normalizeLegacyUrl(url: string) {
  const pathname = getPathname(url)
  const mapped = LEGACY_REDIRECTS[pathname]
  if (!mapped) {
    return url
  }

  const queryIndex = url.indexOf('?')
  return queryIndex === -1 ? mapped : `${mapped}${url.slice(queryIndex)}`
}

function isTabPage(url: string) {
  return TAB_PAGES.has(getPathname(url))
}

function isProfilePage(url: string) {
  return getPathname(url) === PROFILE_PAGE_URL
}

function parseErrorMessage(data: unknown, statusCode: number) {
  if (typeof (data as { detail?: unknown })?.detail === 'string') {
    return (data as { detail: string }).detail
  }
  return `Request failed with ${statusCode}`
}

function persistCurrentUser(user: UserSummary | null) {
  currentUser.value = user
  if (user) {
    saveCurrentUser(user)
  } else {
    clearCurrentUser()
  }
}

export function syncCurrentUser(user: UserSummary | null) {
  persistCurrentUser(user)
}

export function setProfileOnboarded(value: boolean) {
  profileOnboarded.value = value
  saveProfileOnboarded(value)
}

export function isProfileComplete(profile: Pick<ProfileResponse, 'headline' | 'major' | 'grade'>) {
  return Boolean(profile.headline.trim() && profile.major.trim() && profile.grade.trim())
}

async function rawRequest<T>(path: string, options: RawRequestOptions = {}) {
  const { method = 'GET', token = null, data } = options
  const response = await uni.request({
    url: `${BASE_URL}/${path.replace(/^\//, '')}`,
    method,
    data,
    header: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  const statusCode = response.statusCode ?? 0
  if (statusCode < 200 || statusCode >= 300) {
    throw new Error(parseErrorMessage(response.data, statusCode))
  }

  return response.data as T
}

export async function syncProfileOnboardingStatus() {
  const accessToken = getAccessToken()
  if (!accessToken) {
    setProfileOnboarded(false)
    return false
  }

  try {
    const profile = await rawRequest<ProfileResponse>('profile/me/', { token: accessToken })
    const completed = isProfileComplete(profile)
    setProfileOnboarded(completed)
    return completed
  } catch {
    setProfileOnboarded(false)
    return false
  }
}

export function applyLoginResult(payload: LoginResponse) {
  saveAuthTokens(payload.access, payload.refresh)
  accessToken.value = payload.access
  persistCurrentUser(payload.user ?? null)
}

export function clearAuthSession() {
  clearAuthTokens()
  accessToken.value = null
  clearCurrentUser()
  clearLoginRedirect()
  clearProfileOnboarded()
  persistCurrentUser(null)
  profileOnboarded.value = false
}

export async function refreshAccessToken() {
  if (refreshPromise) {
    return refreshPromise
  }

  const refresh = getRefreshToken()
  if (!refresh) {
    clearAuthSession()
    return null
  }

  refreshPromise = rawRequest<{ access: string; refresh?: string }>('auth/refresh/', {
    method: 'POST',
    data: { refresh },
  })
    .then((payload) => {
      saveAccessToken(payload.access)
      accessToken.value = payload.access
      if (payload.refresh) {
        saveAuthTokens(payload.access, payload.refresh)
      }
      return payload.access
    })
    .catch(() => {
      clearAuthSession()
      return null
    })
    .finally(() => {
      refreshPromise = null
    })

  return refreshPromise
}

export async function loadCurrentUser() {
  const accessToken = getAccessToken()
  if (!accessToken) {
    persistCurrentUser(null)
    return null
  }

  try {
    const user = await rawRequest<UserSummary>('auth/me/', { token: accessToken })
    persistCurrentUser(user)
    return user
  } catch {
    persistCurrentUser(null)
    return null
  }
}

export async function bootstrapAuth() {
  if (bootstrapPromise) {
    return bootstrapPromise
  }

  bootstrapPromise = (async () => {
    const storedAccessToken = getAccessToken()
    const refreshToken = getRefreshToken()

    if (!storedAccessToken && !refreshToken) {
      clearAuthSession()
      authReady.value = true
      return
    }

    if (!storedAccessToken && refreshToken) {
      await refreshAccessToken()
    } else {
      accessToken.value = storedAccessToken
    }

    let user = await loadCurrentUser()
    if (!user && getRefreshToken()) {
      const refreshedToken = await refreshAccessToken()
      if (refreshedToken) {
        user = await loadCurrentUser()
      }
    }

    if (!user && !getAccessToken()) {
      clearAuthSession()
    } else if (getAccessToken()) {
      await syncProfileOnboardingStatus()
    }

    authReady.value = true
  })().finally(() => {
    bootstrapPromise = null
  })

  return bootstrapPromise
}

export function redirectToLogin(targetUrl?: string) {
  const currentUrl = getCurrentPageUrl()
  const resolvedTarget = normalizeLegacyUrl(targetUrl ?? currentUrl)

  if (resolvedTarget && !resolvedTarget.startsWith(LOGIN_PAGE_URL)) {
    saveLoginRedirect(resolvedTarget)
  }

  if (currentUrl.startsWith(LOGIN_PAGE_URL)) {
    return
  }

  uni.navigateTo({ url: LOGIN_PAGE_URL })
}

function navigateAfterAuth(url: string) {
  const resolvedUrl = normalizeLegacyUrl(url)
  if (isTabPage(resolvedUrl)) {
    uni.switchTab({
      url: resolvedUrl as '/pages/forum/index' | '/pages/publish/index' | '/pages/messages/index' | '/pages/me/index',
    })
    return
  }
  uni.reLaunch({ url: resolvedUrl })
}

function getResolvedRedirect(fallback = DEFAULT_AUTHED_URL) {
  const redirect = getLoginRedirect()
  clearLoginRedirect()
  return normalizeLegacyUrl(redirect || fallback)
}

export async function completeLogin(user: UserSummary | null) {
  const completed = await syncProfileOnboardingStatus()
  if (!completed) {
    navigateAfterAuth(PROFILE_PAGE_URL)
    return
  }

  navigateAfterAuth(getResolvedRedirect(user ? DEFAULT_AUTHED_URL : DEFAULT_AUTHED_URL))
}

export function ensureAuthenticated(targetUrl?: string) {
  if (!getAccessToken()) {
    redirectToLogin(targetUrl)
    return false
  }

  const resolvedTarget = normalizeLegacyUrl(targetUrl ?? getCurrentPageUrl())
  if (!profileOnboarded.value && resolvedTarget && !isProfilePage(resolvedTarget)) {
    saveLoginRedirect(resolvedTarget)
    uni.navigateTo({ url: PROFILE_PAGE_URL })
    return false
  }

  return true
}

export function finishProfileOnboarding() {
  setProfileOnboarded(true)
  navigateAfterAuth(getResolvedRedirect(DEFAULT_AUTHED_URL))
}

export async function logoutUser() {
  const refresh = getRefreshToken()
  const access = getAccessToken()

  try {
    if (refresh && access) {
      await rawRequest('auth/logout/', {
        method: 'POST',
        token: access,
        data: { refresh },
      })
    }
  } catch {
    // Ignore logout API failures and clear the local session anyway.
  } finally {
    clearAuthSession()
  }
}
