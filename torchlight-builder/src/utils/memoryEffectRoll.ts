import type { MemorySelectionItem } from '@/stores/build'

/** 追忆文案中的范围：半角/全角括号 + 数字 + en-dash(–)/hyphen(-) */
const RANGE_IN_PARENS_RE = /\(([+-]?\d+(?:\.\d+)?)\s*[–\-]\s*([+-]?\d+(?:\.\d+)?)\)/g

export function listNumericRangesInEffectText(text: string): Array<{ min: number; max: number }> {
  const out: Array<{ min: number; max: number }> = []
  let m: RegExpExecArray | null
  const re = new RegExp(RANGE_IN_PARENS_RE.source, 'g')
  while ((m = re.exec(text)) != null) {
    const a = Number(m[1])
    const b = Number(m[2])
    if (!Number.isFinite(a) || !Number.isFinite(b)) continue
    out.push({ min: Math.min(a, b), max: Math.max(a, b) })
  }
  return out
}

export function defaultRangePicks(ranges: Array<{ min: number; max: number }>): number[] {
  return ranges.map(r => Math.round((r.min + r.max) / 2))
}

export function integerOptionsForRange(min: number, max: number): number[] {
  const lo = Math.ceil(min)
  const hi = Math.floor(max)
  const o: number[] = []
  for (let x = lo; x <= hi; x++) o.push(x)
  return o
}

/** 将各段范围依次替换为选中的数字（字符串形式，保留游戏原文前后缀） */
export function applyRangePicksToEffectText(template: string, picks: number[]): string {
  let i = 0
  return template.replace(/\(([+-]?\d+(?:\.\d+)?)\s*[–\-]\s*([+-]?\d+(?:\.\d+)?)\)/g, (_full, a: string, b: string) => {
    const min = Math.min(Number(a), Number(b))
    const max = Math.max(Number(a), Number(b))
    let v = picks[i++]
    if (!Number.isFinite(v)) v = Math.round((min + max) / 2)
    const n = Math.round(v as number)
    const clamped = Math.min(max, Math.max(min, n))
    return String(clamped)
  })
}

function memoryItemBase(item: MemorySelectionItem): Omit<MemorySelectionItem, 'effectText' | 'effectTextRaw' | 'rangePicks'> {
  return {
    modifierId: item.modifierId,
    sourceId: item.sourceId,
    sourceName: item.sourceName,
    sourcePath: item.sourcePath,
    category: item.category,
    tier: item.tier,
    tierLabel: item.tierLabel,
    level: item.level,
    weight: item.weight,
    memoryRarity: item.memoryRarity
  }
}

export function normalizeMemorySelectionItem(item: MemorySelectionItem): MemorySelectionItem {
  const raw = String(item.effectTextRaw ?? item.effectText ?? '').trim()
  const ranges = listNumericRangesInEffectText(raw)
  const base = memoryItemBase(item)
  if (ranges.length === 0) {
    return { ...base, effectText: raw }
  }
  let picks = item.rangePicks
  if (!picks || picks.length !== ranges.length) {
    picks = defaultRangePicks(ranges)
  } else {
    picks = picks.map((p, i) => {
      const r = ranges[i]!
      if (!Number.isFinite(p)) return Math.round((r.min + r.max) / 2)
      const n = Math.round(p)
      return Math.min(r.max, Math.max(r.min, n))
    })
  }
  const effectText = applyRangePicksToEffectText(raw, picks)
  return {
    ...base,
    effectText,
    effectTextRaw: raw,
    rangePicks: picks
  }
}

/** 用于 UI：原文片段与范围下拉交错，下拉直接替代原 (a–b) 位置 */
export type MemoryEffectInlineSegment =
  | { type: 'text'; value: string }
  | { type: 'range'; rangeIndex: number; options: number[]; current: number }

export function memoryEffectInlineSegments(item: MemorySelectionItem): MemoryEffectInlineSegment[] {
  const raw = String(item.effectTextRaw ?? item.effectText ?? '').trim()
  const picks = item.rangePicks ?? []
  const re = /\(([+-]?\d+(?:\.\d+)?)\s*[–\-]\s*([+-]?\d+(?:\.\d+)?)\)/g
  const segments: MemoryEffectInlineSegment[] = []
  let lastIndex = 0
  let rangeIndex = 0
  let m: RegExpExecArray | null
  const g = new RegExp(re.source, 'g')
  while ((m = g.exec(raw)) != null) {
    if (m.index > lastIndex) {
      segments.push({ type: 'text', value: raw.slice(lastIndex, m.index) })
    }
    const a = Number(m[1])
    const b = Number(m[2])
    if (!Number.isFinite(a) || !Number.isFinite(b)) {
      lastIndex = m.index + m[0].length
      continue
    }
    const min = Math.min(a, b)
    const max = Math.max(a, b)
    const options = integerOptionsForRange(min, max)
    let current = picks[rangeIndex]
    if (!Number.isFinite(current)) current = Math.round((min + max) / 2)
    current = Math.min(max, Math.max(min, Math.round(current as number)))
    segments.push({ type: 'range', rangeIndex: rangeIndex++, options, current })
    lastIndex = m.index + m[0].length
  }
  if (lastIndex < raw.length) {
    segments.push({ type: 'text', value: raw.slice(lastIndex) })
  }
  if (segments.length === 0) {
    segments.push({ type: 'text', value: String(item.effectText ?? raw) || '—' })
  }
  return segments
}

export function patchMemoryItemRangePick(
  item: MemorySelectionItem,
  rangeIndex: number,
  value: number
): MemorySelectionItem {
  const raw = String(item.effectTextRaw ?? item.effectText ?? '').trim()
  const ranges = listNumericRangesInEffectText(raw)
  if (!ranges.length || rangeIndex < 0 || rangeIndex >= ranges.length) return item
  const picks = [...(item.rangePicks ?? defaultRangePicks(ranges))]
  const r = ranges[rangeIndex]!
  const v = Math.min(r.max, Math.max(r.min, Math.round(value)))
  picks[rangeIndex] = v
  return normalizeMemorySelectionItem({
    ...item,
    effectTextRaw: raw,
    rangePicks: picks
  })
}
