import { BASE_URL } from '../constants'
import { redirectToLogin, refreshAccessToken } from './auth'
import { getAccessToken } from './storage'

export type RequestOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  data?: Record<string, unknown> | string | undefined
  auth?: boolean
  headers?: Record<string, string>
  timeout?: number
}

async function sendRequest(
  url: string,
  method: NonNullable<RequestOptions['method']>,
  data: RequestOptions['data'],
  token: string | null,
  headers: Record<string, string>,
  timeout: number,
) {
  try {
    return await uni.request({
      url,
      method: method as UniApp.RequestOptions['method'],
      data,
      timeout,
      header: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...headers,
      },
    })
  } catch (error) {
    const message =
      typeof (error as { errMsg?: unknown })?.errMsg === 'string'
        ? (error as { errMsg: string }).errMsg
        : '请求服务失败，请稍后重试'
    throw new Error(message)
  }
}

export async function request<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const { method = 'GET', data, auth = true, headers = {}, timeout = 15000 } = options
  const url = `${BASE_URL}/${path.replace(/^\//, '')}`
  let token = auth ? getAccessToken() : null
  let response = await sendRequest(url, method, data, token, headers, timeout)

  if (auth && response.statusCode === 401) {
    const refreshedToken = await refreshAccessToken()
    if (refreshedToken) {
      token = refreshedToken
      response = await sendRequest(url, method, data, token, headers, timeout)
    } else {
      redirectToLogin()
    }
  }

  const statusCode = response.statusCode ?? 0
  if (statusCode < 200 || statusCode >= 300) {
    const detail =
      typeof (response.data as { detail?: unknown })?.detail === 'string'
        ? (response.data as { detail: string }).detail
        : `Request failed with ${statusCode}`
    throw new Error(detail)
  }

  return response.data as T
}

export function getAdminUrl() {
  return BASE_URL.replace(/\/api\/v1\/?$/, '') + '/admin/'
}
