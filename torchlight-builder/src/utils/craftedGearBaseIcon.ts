import { resolveLegendaryGearIconUrl } from '@/utils/legendaryGearIcon'

/** 打造基底图标：优先本地 `/assets/equipment/crafted-bases/...`，否则回退 CDN */
export function resolveCraftedGearBaseIconUrl(base: {
  id: string
  iconUrl?: string
  cdnIconUrl?: string
  localIconUrl?: string
}): string {
  return resolveLegendaryGearIconUrl(base)
}
