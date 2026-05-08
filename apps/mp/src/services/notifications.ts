import type { NotificationItem } from '../types/api'
import { request } from '../utils/request'

export function fetchNotifications(unreadOnly = false) {
  const suffix = unreadOnly ? '?unread=1' : ''
  return request<NotificationItem[]>(`notifications/${suffix}`)
}

export function fetchNotificationUnreadCount() {
  return request<{ unread_count: number }>('notifications/unread-count/')
}

export function markNotificationRead(notificationId: string) {
  return request<NotificationItem>(`notifications/${notificationId}/`, {
    method: 'PATCH',
    data: { is_read: true },
  })
}

export function markAllNotificationsRead() {
  return request<{ detail: string }>('notifications/mark-all-read/', {
    method: 'POST',
  })
}
