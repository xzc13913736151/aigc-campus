import { fetchUserProfile } from '../services/profile'

type AvatarCacheEntry = {
  avatarUrl: string
  expiresAt: number
}

const CACHE_TTL = 2 * 60 * 1000
const avatarCache = new Map<string, AvatarCacheEntry>()
const avatarRequests = new Map<string, Promise<string>>()

export function getCachedAvatar(userId: string) {
  const cached = avatarCache.get(userId)
  if (!cached || cached.expiresAt <= Date.now()) {
    return ''
  }
  return cached.avatarUrl
}

export async function resolveProfileAvatar(userId: string) {
  if (!userId) {
    return ''
  }

  const cached = avatarCache.get(userId)
  if (cached && cached.expiresAt > Date.now()) {
    return cached.avatarUrl
  }

  const pending = avatarRequests.get(userId)
  if (pending) {
    return pending
  }

  const request = fetchUserProfile(userId)
    .then((profile) => {
      const avatarUrl = profile.avatar_url || ''
      avatarCache.set(userId, {
        avatarUrl,
        expiresAt: Date.now() + CACHE_TTL,
      })
      return avatarUrl
    })
    .finally(() => {
      avatarRequests.delete(userId)
    })

  avatarRequests.set(userId, request)
  return request
}

