type ChooseImageOptions = {
  count?: number
  sourceType?: Array<'album' | 'camera'>
}

function normalizeImagePaths(paths: Array<string | undefined | null>) {
  return paths.filter((path): path is string => Boolean(path))
}

export async function chooseImagePaths(options: ChooseImageOptions = {}) {
  const { count = 1, sourceType = ['album', 'camera'] } = options

  // App 端 chooseMedia 兼容性不如 chooseImage，优先走更稳的图片 API。
  // #ifndef MP-WEIXIN
  const image = await uni.chooseImage({
    count,
    sizeType: ['compressed'],
    sourceType,
  })
  return normalizeImagePaths(image.tempFilePaths ?? [])
  // #endif

  // #ifdef MP-WEIXIN
  const media = (await uni.chooseMedia({
    count,
    mediaType: ['image'],
    sizeType: ['compressed'],
    sourceType,
  })) as unknown as UniApp.ChooseMediaSuccessCallbackResult
  return normalizeImagePaths(media.tempFiles?.map((file) => file.tempFilePath) ?? [])
  // #endif
}
