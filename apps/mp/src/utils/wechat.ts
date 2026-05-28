export async function getWechatLoginCode() {
  let code = ''

  try {
    const result = await uni.login({ provider: 'weixin' })
    code = result.code ?? ''
  } catch {
    code = ''
  }

  if (code) {
    return code
  }

  throw new Error('未获取到微信登录凭证，请稍后重试')
}
