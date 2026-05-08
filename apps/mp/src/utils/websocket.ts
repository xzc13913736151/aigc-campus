import { BASE_URL } from '../constants'
import { getAccessToken } from './storage'

type SocketHandlers = {
  onOpen?: () => void
  onMessage?: (data: unknown) => void
  onError?: () => void
  onClose?: () => void
}

function getWebSocketBaseUrl() {
  if (BASE_URL.startsWith('https://')) {
    return BASE_URL.replace(/^https:\/\//, 'wss://').replace(/\/api\/v1\/?$/, '')
  }
  return BASE_URL.replace(/^http:\/\//, 'ws://').replace(/\/api\/v1\/?$/, '')
}

function safeParseMessage(raw: string | ArrayBuffer) {
  if (typeof raw !== 'string') {
    return raw
  }

  try {
    return JSON.parse(raw) as unknown
  } catch {
    return raw
  }
}

export function connectAuthedSocket(path: string, handlers: SocketHandlers = {}) {
  const token = getAccessToken()
  if (!token) {
    return null
  }

  const socket = uni.connectSocket({
    url: `${getWebSocketBaseUrl()}${path}?token=${encodeURIComponent(token)}`,
    complete: () => undefined,
  })

  socket.onOpen(() => {
    handlers.onOpen?.()
  })
  socket.onMessage((event) => {
    handlers.onMessage?.(safeParseMessage(event.data))
  })
  socket.onError(() => {
    handlers.onError?.()
  })
  socket.onClose(() => {
    handlers.onClose?.()
  })

  return socket
}
