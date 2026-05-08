export function showToast(title: string, icon: 'none' | 'success' | 'error' = 'none') {
  uni.showToast({ title, icon, duration: 2200 })
}
