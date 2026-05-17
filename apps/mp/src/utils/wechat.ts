export async function getWechatLoginCode() {
  let code = ''

  try {
    const result = await uni.login({ provider: 'weixin' })
    code = result.code ?? ''
  } catch {
    code = ''
  }

  if (!code) {
    return 'demo-wechat-login-code'
  }

  return code
}
