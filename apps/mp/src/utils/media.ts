import { BASE_URL } from '../constants'

const API_PREFIX_PATTERN = /\/api\/v1\/?$/

export function getMediaUrl(url?: string | null) {
  const value = (url ?? '').trim()
  if (!value) {
    return ''
  }
  if (/^(https?:|wxfile:|file:|blob:|data:)/i.test(value)) {
    return value
  }

  const origin = BASE_URL.replace(API_PREFIX_PATTERN, '')
  return `${origin}${value.startsWith('/') ? value : `/${value}`}`
}

export function getMediaUrls(urls: string[]) {
  return urls.map((url) => getMediaUrl(url)).filter(Boolean)
}
