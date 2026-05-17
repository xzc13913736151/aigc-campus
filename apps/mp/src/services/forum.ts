import type { ForumComment, ForumPost, UserSummary } from '../types/api'
import { uploadFile } from '../utils/upload'
import { request } from '../utils/request'
import { buildQuery } from '../utils/query'

const mockAuthor: UserSummary = {
  id: 'mock-user-campus-helper',
  email: 'campus-helper@example.com',
  full_name: 'CampusClaw 小助手',
  nickname: '校园小助手',
  role: 'student',
  is_email_verified: true,
  email_verified_at: '2026-05-08T09:00:00Z',
  created_at: '2026-05-08T09:00:00Z',
  updated_at: '2026-05-08T09:00:00Z',
}

const mockForumPosts: ForumPost[] = [
  {
    id: 'mock-forum-post-1',
    author: mockAuthor,
    title: '周末有人一起去图书馆自习吗？',
    summary: '想找几位同学周末一起自习，互相监督，也可以顺便交流课程资料。',
    body: '这周六下午准备去图书馆三楼自习，主要复习高数和英语。欢迎想一起学习、互相监督的同学加入。',
    category: '学习交流',
    tags: ['自习', '图书馆', '学习搭子'],
    is_deleted: false,
    is_liked: false,
    like_count: 12,
    comment_count: 3,
    comments: [],
    image_urls: [],
    created_at: '2026-05-08T10:30:00Z',
    updated_at: '2026-05-08T10:30:00Z',
  },
  {
    id: 'mock-forum-post-2',
    author: mockAuthor,
    title: '招募 AI 校园助手项目队友',
    summary: '准备做一个校园问答和信息整理小程序，想找前端、后端和产品同学一起推进。',
    body: '项目方向是把校园常见问题、活动信息和学习资源整合到一个 AI 助手里。目前已有初步想法，想组 3-4 人小队一起做原型。',
    category: '项目合作',
    tags: ['AI', '小程序', '组队'],
    is_deleted: false,
    is_liked: true,
    like_count: 28,
    comment_count: 6,
    comments: [],
    image_urls: [],
    created_at: '2026-05-08T08:45:00Z',
    updated_at: '2026-05-08T08:45:00Z',
  },
]

function filterMockForumPosts(query: string, category: string) {
  const normalizedQuery = query.trim().toLowerCase()
  return mockForumPosts.filter((post) => {
    const matchesCategory = !category || post.category === category
    const matchesQuery =
      !normalizedQuery ||
      [post.title, post.summary, post.body, post.category, ...post.tags].some((value) =>
        value.toLowerCase().includes(normalizedQuery),
      )

    return matchesCategory && matchesQuery
  })
}

export async function fetchForumPosts(query = '', category = '') {
  try {
    return await request<ForumPost[]>(`forum/posts/${buildQuery({ q: query, category })}`, { auth: false })
  } catch {
    return filterMockForumPosts(query, category)
  }
}

export async function fetchForumPostDetail(postId: string) {
  const mockPost = mockForumPosts.find((post) => post.id === postId)
  if (mockPost) {
    return mockPost
  }

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

export function createForumComment(postId: string, payload: { body: string; parent?: string | null }) {
  return request<ForumComment>(`forum/posts/${postId}/comments/`, {
    method: 'POST',
    data: payload,
  })
}

export function uploadForumPostImage(postId: string, filePath: string) {
  return uploadFile<{ id: string; image_url: string }>(`forum/posts/${postId}/images/`, filePath, 'image')
}
