export async function getWechatLoginCode() {
  const result = await uni.login({ provider: 'weixin' })
  const code = result.code ?? ''
  if (!code) {
    throw new Error('未能获取微信登录凭证，请重试')
  }
  return code
}
