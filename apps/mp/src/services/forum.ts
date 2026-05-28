import type { ForumComment, ForumPost } from '../types/api'
import { uploadFile } from '../utils/upload'
import { request } from '../utils/request'
import { buildQuery } from '../utils/query'

export function fetchForumPosts(query = '', category = '') {
  return request<ForumPost[]>(`forum/posts/${buildQuery({ q: query, category })}`, { auth: false })
}

export function fetchForumPostDetail(postId: string) {
  return request<ForumPost>(`forum/posts/${postId}/`, { auth: false })
}

export function fetchMyForumPosts() {
  return request<ForumPost[]>('forum/posts/mine/')
}

export function createForumPost(payload: { title: string; body: string; category: string; tags: string[] }) {
  return request<ForumPost>('forum/posts/', {
    method: 'POST',
    data: payload,
  })
}

export function updateForumPost(postId: string, payload: Partial<Pick<ForumPost, 'title' | 'body' | 'category' | 'tags'>>) {
  return request<ForumPost>(`forum/posts/${postId}/`, {
    method: 'PATCH',
    data: payload,
  })
}

export function deleteForumPost(postId: string) {
  return request<void>(`forum/posts/${postId}/`, {
    method: 'DELETE',
  })
}

export function toggleForumPostLike(postId: string) {
  return request<{ liked: boolean; like_count: number }>(`forum/posts/${postId}/like/`, {
    method: 'POST',
  })
}

export function toggleForumCommentLike(commentId: string) {
  return request<{ liked: boolean; like_count: number }>(`forum/comments/${commentId}/like/`, {
    method: 'POST',
  }).catch((error) => {
    if (error instanceof Error && error.message.includes('404')) {
      return request<{ liked: boolean; like_count: number }>(`forum/comment-likes/${commentId}/`, {
        method: 'POST',
      })
    }
    throw error
  })
}

export function createForumComment(postId: string, payload: { body: string; parent?: string | null }) {
  return request<ForumComment>(`forum/posts/${postId}/comments/`, {
    method: 'POST',
    data: payload,
  })
}

export function uploadForumPostImage(postId: string, filePath: string) {
  return uploadFile<{ id: string; image_url: string }>(`forum/posts/${postId}/images/`, filePath, 'image')
}
