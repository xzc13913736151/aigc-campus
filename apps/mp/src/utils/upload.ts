import { BASE_URL } from '../constants'
import { getAccessToken } from './storage'

export async function uploadFile<T>(path: string, filePath: string, formName = 'file') {
  const token = getAccessToken()
  const result = await uni.uploadFile({
    url: `${BASE_URL}/${path.replace(/^\//, '')}`,
    filePath,
    name: formName,
    timeout: 15000,
    header: token ? { Authorization: `Bearer ${token}` } : {},
  })

  const data = typeof result.data === 'string' ? JSON.parse(result.data || '{}') : result.data
  if (result.statusCode < 200 || result.statusCode >= 300) {
    const detail = typeof data?.detail === 'string' ? data.detail : 'Upload failed.'
    throw new Error(detail)
  }

  return data as T
}

export async function chooseMediaAndUpload<T>(path: string, formName = 'file') {
  const media = (await uni.chooseMedia({
    count: 1,
    mediaType: ['image'],
    sizeType: ['compressed'],
    sourceType: ['album', 'camera'],
  })) as unknown as UniApp.ChooseMediaSuccessCallbackResult

  const file = media.tempFiles?.[0]
  if (!file?.tempFilePath) {
    throw new Error('No file selected.')
  }

  return uploadFile<T>(path, file.tempFilePath, formName)
}
