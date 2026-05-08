export function buildQuery(params: Record<string, unknown>) {
  const query = Object.entries(params)
    .filter(([, value]) => value !== undefined && value !== null && String(value).trim() !== '')
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value).trim())}`)
    .join('&')

  return query ? `?${query}` : ''
}
