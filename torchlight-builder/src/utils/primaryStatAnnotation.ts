/**
 * 根据效果原文中的「每点力量/敏捷/智慧」句式，生成展示用后缀（仅标注装备粗算属性，具体乘算结果在列表右侧 pct 列）。
 */

export type PrimaryStatsSnapshot = {
  力量: number
  敏捷: number
  智慧: number
}

function fmtAnno(n: number): string {
  if (!Number.isFinite(n)) return '—'
  return n.toLocaleString('zh-CN', { maximumFractionDigits: 4, useGrouping: true })
}

/**
 * 当行内存在「每 N 点力量/敏捷/智慧」或「+N 每点…」时，括号内只列出涉及到的属性及装备粗算值。
 */
export function perPointPrimaryAnnotationSuffix(line: string, stats: PrimaryStatsSnapshot): string {
  const compact = String(line ?? '').replace(/\s+/g, '')
  if (!compact) return ''
  const attrs = new Set<keyof PrimaryStatsSnapshot>()
  const reEvery = /每(?:\d+(?:\.\d+)?)?点(力量|敏捷|智慧)/g
  let m: RegExpExecArray | null
  while ((m = reEvery.exec(compact)) !== null) {
    attrs.add(m[1] as keyof PrimaryStatsSnapshot)
  }
  const reLegacy = /([+＋]?\d+(?:\.\d+)?)每点(力量|敏捷|智慧)/g
  while ((m = reLegacy.exec(compact)) !== null) {
    const am = /每点(力量|敏捷|智慧)$/.exec(m[0])
    if (am) attrs.add(am[1] as keyof PrimaryStatsSnapshot)
  }
  if (attrs.size === 0) return ''
  const parts: string[] = []
  for (const attr of ['力量', '敏捷', '智慧'] as const) {
    if (attrs.has(attr)) parts.push(`${attr}${fmtAnno(stats[attr])}`)
  }
  return `（装备粗算 ${parts.join('；')}）`
}
