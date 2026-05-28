export type NavTarget =
  | '/pages/forum/index'
  | '/pages/publish/index'
  | '/pages/messages/index'
  | '/pages/me/index'
  | '/pages/auth/login'
  | '/pages/auth/register'
  | '/pages/profile/index'
  | '/pages/blocks/index'
  | '/pages/teammates/index'
  | '/pages/dating/index'
  | '/pages/forum/detail'
  | '/pages/forum/create'
  | '/pages/chat/index'
  | '/pages/admin/index'
  | '/pages/assistant/index'
  | '/pages/trade/index'
  | '/pages/trade/create'
  | '/pages/trade/detail'
  | '/pages/trade/mine'
  | '/pages/trade/matches'

type TabTarget = Extract<NavTarget, '/pages/forum/index' | '/pages/publish/index' | '/pages/messages/index' | '/pages/me/index'>
type StackTarget = Exclude<NavTarget, TabTarget>
type StackUrl = StackTarget | `${StackTarget}?${string}`

export function navigateTo(url: StackUrl) {
  uni.navigateTo({ url })
}

export function switchTab(url: TabTarget) {
  uni.switchTab({ url })
}
