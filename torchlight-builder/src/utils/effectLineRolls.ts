/**
 * 解析装备词条中的「数值区间」，用于在 UI 中以下拉框选择具体数值。
 * 支持：(35–39)、(35-39)、以及不在括号内的 12 - 12（两侧为数字、中间为 ASCII 减号）。
 */

export type EffectRollSegment =
  | { type: 'text'; text: string }
  | { type: 'pick'; options: string[] }

/** 括号内范围：Unicode 减号 (U+2013) 或 ASCII - */
const PAREN_RANGE_RE = /\((-?\d+(?:\.\d+)?)\s*(?:\u2013|-)\s*(-?\d+(?:\.\d+)?)\)/g

/** 两侧数字 + 空格 + ASCII - + 空格（不与括号内范围重叠） */
const SPACED_PAIR_RE = /(-?\d+(?:\.\d+)?)\s+-\s+(-?\d+(?:\.\d+)?)/g

const MAX_INTEGER_SPAN = 220

function expandNumericRange(lo: number, hi: number): string[] {
  const a = Math.min(lo, hi)
  const b = Math.max(lo, hi)
  if (!Number.isFinite(a) || !Number.isFinite(b)) return []
  if (Number.isInteger(a) && Number.isInteger(b)) {
    const span = b - a
    if (span > MAX_INTEGER_SPAN) {
      return [String(a), String(b)]
    }
    const out: string[] = []
    for (let i = a; i <= b; i++) out.push(String(i))
    return out
  }
  if (Math.abs(b - a) < 1e-9) return [trimNumStr(a)]
  const out: string[] = []
  const step = b - a <= 1 ? 0.1 : 0.5
  const maxOpts = 80
  for (let x = a, n = 0; x <= b + 1e-9 && n < maxOpts; x += step, n++) {
    out.push(trimNumStr(x))
  }
  return dedupeOptions(out)
}

function trimNumStr(n: number): string {
  const s = n.toFixed(2).replace(/\.?0+$/, '')
  return s === '-0' ? '0' : s
}

function dedupeOptions(opts: string[]): string[] {
  const seen = new Set<string>()
  return opts.filter(o => {
    if (seen.has(o)) return false
    seen.add(o)
    return true
  })
}

type RangeMatch = { start: number; end: number; lo: number; hi: number }

function rangesOverlap(a: RangeMatch, b: RangeMatch): boolean {
  return !(a.end <= b.start || a.start >= b.end)
}

function collectParenRanges(line: string): RangeMatch[] {
  const out: RangeMatch[] = []
  PAREN_RANGE_RE.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = PAREN_RANGE_RE.exec(line)) !== null) {
    const lo = parseFloat(m[1]!)
    const hi = parseFloat(m[2]!)
    if (!Number.isFinite(lo) || !Number.isFinite(hi)) continue
    out.push({ start: m.index, end: m.index + m[0].length, lo, hi })
  }
  return out
}

function collectSpacedPairRanges(line: string, blocked: RangeMatch[]): RangeMatch[] {
  const out: RangeMatch[] = []
  SPACED_PAIR_RE.lastIndex = 0
  let m: RegExpExecArray | null
  while ((m = SPACED_PAIR_RE.exec(line)) !== null) {
    const start = m.index
    const end = m.index + m[0].length
    const cand: RangeMatch = {
      start,
      end,
      lo: parseFloat(m[1]!),
      hi: parseFloat(m[2]!)
    }
    if (!Number.isFinite(cand.lo) || !Number.isFinite(cand.hi)) continue
    const inside = blocked.some(b => rangesOverlap(cand, b))
    if (inside) continue
    out.push(cand)
  }
  return out
}

/**
 * 若包含可滚动的数值区间则返回分段；否则返回 null（整行按纯文本展示）。
 */
export function parseEffectLineRolls(line: string): EffectRollSegment[] | null {
  const trimmed = line.trim()
  if (!trimmed) return null

  // 武器白字「最小 - 最大 物理伤害」：中间减号是 DPS 面板的固定格式，不是可调数值区间。
  // 若被 SPACED_PAIR_RE 当成 (lo-hi) 区间代入，会变成「6 物理伤害」等，导致 weaponPhysicalFromEquipment 无法解析白字。
  const withoutLineTag = trimmed.replace(/^\[[^\]]+\]\s*/, '')
  if (/^\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*物理伤害\s*$/.test(withoutLineTag)) {
    return null
  }

  const paren = collectParenRanges(trimmed)
  const pairs = collectSpacedPairRanges(trimmed, paren)
  const all = [...paren, ...pairs].sort((x, y) => x.start - y.start)
  const merged: RangeMatch[] = []
  for (const r of all) {
    const last = merged[merged.length - 1]
    if (last && r.start < last.end) continue
    merged.push(r)
  }

  if (merged.length === 0) return null

  const segments: EffectRollSegment[] = []
  let pos = 0
  for (const r of merged) {
    if (r.start > pos) {
      segments.push({ type: 'text', text: trimmed.slice(pos, r.start) })
    }
    const options = expandNumericRange(r.lo, r.hi)
    if (options.length === 0) {
      segments.push({ type: 'text', text: trimmed.slice(r.start, r.end) })
    } else {
      segments.push({ type: 'pick', options })
    }
    pos = r.end
  }
  if (pos < trimmed.length) {
    segments.push({ type: 'text', text: trimmed.slice(pos) })
  }

  if (!segments.some(s => s.type === 'pick')) return null
  return segments
}

/**
 * 将一行词条按装备页 `EffectLineRollPicker` 的规则代入下拉选中值（无选择时用区间首项，与 UI 一致）。
 */
export function resolveEffectLineWithRollPicks(
  line: string,
  pickKeyPrefix: string,
  selections: Record<string, string>
): string {
  const segs = parseEffectLineRolls(line)
  if (!segs) return line
  let pickIdx = 0
  let out = ''
  for (const s of segs) {
    if (s.type === 'text') {
      out += s.text
    } else {
      const k = `${pickKeyPrefix}#${pickIdx}`
      pickIdx++
      const cur = selections[k]
      const v = cur !== undefined && s.options.includes(cur) ? cur : (s.options[0] ?? '')
      out += v
    }
  }
  return out
}
