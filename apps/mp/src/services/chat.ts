import type { ChatMessage, ChatThread } from '../types/api'
import { request } from '../utils/request'

export function fetchChatThreads() {
  return request<ChatThread[]>('chat/threads/')
}

export function createChatThread(payload: { target_user_id: string; source_type?: string; source_id?: string }) {
  return request<ChatThread>('chat/threads/', {
    method: 'POST',
    data: payload,
  })
}

export function fetchChatMessages(threadId: string) {
  return request<{ thread: ChatThread; messages: ChatMessage[] }>(`chat/threads/${threadId}/messages/`)
}

export function sendChatMessage(threadId: string, payload: { body: string }) {
  return request<ChatMessage>(`chat/threads/${threadId}/messages/`, {
    method: 'POST',
    data: payload,
  })
}

export function markChatThreadRead(threadId: string) {
  return request<{ detail: string }>(`chat/threads/${threadId}/mark-read/`, {
    method: 'POST',
    data: { mark_read: true },
  })
}

export function withdrawChatMessage(threadId: string, messageId: string) {
  return request<ChatMessage>(`chat/threads/${threadId}/messages/${messageId}/withdraw/`, {
    method: 'POST',
    data: { withdraw: true },
  })
}

export function hideChatThread(threadId: string) {
  return request<{ detail: string }>(`chat/threads/${threadId}/hide/`, {
    method: 'POST',
  })
}
