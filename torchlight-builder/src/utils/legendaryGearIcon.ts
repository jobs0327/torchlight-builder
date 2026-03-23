/**
 * 暗金装备图标：`iconUrl` 已为本地路径（/assets/...）时直接使用；
 * 否则回退 legacy `localIconUrl`，再回退 CDN（`iconUrl` 或 `cdnIconUrl`）。
 */
export function resolveLegendaryGearIconUrl(item: {
  id: string
  iconUrl?: string
  cdnIconUrl?: string
  localIconUrl?: string
}): string {
  const primary = item.iconUrl?.trim() ?? ''
  if (primary.startsWith('/')) return primary
  const legacyLocal = item.localIconUrl?.trim()
  if (legacyLocal) return legacyLocal
  if (primary.startsWith('http')) return primary
  return item.cdnIconUrl?.trim() ?? ''
}
