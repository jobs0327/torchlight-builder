/**
 * 从 BD 多来源效果文案中解析「伤害转化」类词条（独立模块，不参与当前简化 DPS 连乘）。
 *
 * 来源示例：装备已选效果、天赋已加点原文、追忆、契灵 effectLines、英雄已选特性描述等。
 * 识别「X% … 转化为 …」以及无百分比的「… 转化为 …」（如「物理伤害转化为火焰伤害」）。
 */

import { getResolvedEffectLinesForEquipmentSlot } from '@/utils/weaponPhysicalFromEquipment'

function norm(s: string): string {
  return s.replace(/[–—]/g, '-').trim()
}

function stripLeadingEffectLineTag(s: string): string {
  return norm(s).replace(/^\[[^\]]+\]\s*/, '')
}

/** 去掉天赋合并展示后缀「 x3」等，避免干扰「转化为」解析 */
function stripTrailingRepeatCountSuffix(s: string): string {
  return s.replace(/\s+x\d+$/i, '').trim()
}

function stripHtml(s: string): string {
  return s.replace(/<[^>]*>/g, '')
}

/**
 * 装备 / 追忆 / 契灵等原始行：去标签、HTML、合并后缀，再交给 parseDamageConversionSegmentsFromLine。
 */
export function normalizeEffectLineForDamageConversion(raw: string): string {
  let s = stripLeadingEffectLineTag(String(raw ?? ''))
  s = stripHtml(s)
  s = stripTrailingRepeatCountSuffix(s)
  return norm(s).replace(/\s+/g, ' ')
}

export type DamageConversionSegment = {
  /**
   * 转化比例（%）；未在文案中写出百分数时为 `null`（如「物理伤害转化为火焰伤害」）。
   */
  pct: number | null
  /** 「转化为」左侧摘要（多为来源伤害类型或条件） */
  fromSnippet: string
  /** 「转化为」右侧摘要（目标伤害类型等） */
  toSnippet: string
}

/** 统一展示块（装备格 / 天赋 / 追忆 / 契灵 / 英雄特性等） */
export type DamageConversionEntry = {
  /** :key，如 equipment-0、talent、memory、pact-xxx */
  id: string
  /** 区块标题 */
  label: string
  segments: DamageConversionSegment[]
  /** 原始行（规范化后），便于核对 */
  sourceLines: string[]
}

export type DamageConversionBuildEstimate = {
  entries: DamageConversionEntry[]
  hasAny: boolean
  segmentCount: number
}

/** @deprecated 使用 DamageConversionEntry */
export type DamageConversionSlotEntry = {
  slotIndex: number
  segments: DamageConversionSegment[]
  sourceLines: string[]
}

/** @deprecated 使用 DamageConversionBuildEstimate */
export type DamageConversionEquipmentEstimate = {
  entries: DamageConversionSlotEntry[]
  hasAny: boolean
  segmentCount: number
}

export type DamageConversionSourceBundle = {
  id: string
  label: string
  lines: readonly string[]
}

function collectSegmentsFromRawLines(lines: readonly string[]): {
  segments: DamageConversionSegment[]
  sourceLines: string[]
} {
  const segments: DamageConversionSegment[] = []
  const sourceLines: string[] = []
  for (const raw of lines) {
    const line = normalizeEffectLineForDamageConversion(raw)
    if (!line.includes('转化为')) continue
    const parsed = parseDamageConversionSegmentsFromLine(line)
    if (parsed.length) {
      segments.push(...parsed)
      sourceLines.push(line)
    }
  }
  return { segments, sourceLines }
}

/**
 * 从单行中抠出 0..n 条转化：
 * - 「数字% … 转化为 …」
 * - 「… 转化为 …」（无百分数，pct 为 null）
 * 先按 ，、, 拆句；若整行无法拆中再对整行尝试一次。
 */
export function parseDamageConversionSegmentsFromLine(line: string): DamageConversionSegment[] {
  const t = norm(line).replace(/\s+/g, ' ')
  const chunks = t.split(/[，,、]/).map(c => c.trim()).filter(Boolean)
  const out: DamageConversionSegment[] = []

  const tryChunk = (chunk: string) => {
    if (!chunk.includes('转化为')) return

    const pctRe = /([+-]?\d+(?:\.\d+)?)\s*%\s*(.+?)转化为\s*(.+)$/
    const pm = chunk.match(pctRe)
    if (pm) {
      const pct = parseFloat(pm[1]!)
      if (Number.isFinite(pct)) {
        const fromSnippet = pm[2]!.trim()
        const toSnippet = pm[3]!.trim()
        if (fromSnippet && toSnippet) {
          out.push({ pct, fromSnippet, toSnippet })
          return
        }
      }
    }

    const nm = chunk.match(/^(.+?)转化为(.+)$/)
    if (nm) {
      const fromSnippet = nm[1]!.trim()
      const toSnippet = nm[2]!.trim()
      if (fromSnippet && toSnippet) out.push({ pct: null, fromSnippet, toSnippet })
    }
  }

  for (const c of chunks) tryChunk(c)
  if (out.length === 0 && t.includes('转化为')) tryChunk(t)
  return out
}

/**
 * 合并多组效果行（装备、天赋、追忆等），只保留解析到至少一条转化的区块。
 */
export function estimateDamageConversionFromSourceBundles(
  bundles: readonly DamageConversionSourceBundle[]
): DamageConversionBuildEstimate {
  const entries: DamageConversionEntry[] = []
  let segmentCount = 0
  for (const b of bundles) {
    if (!b.lines.length) continue
    const { segments, sourceLines } = collectSegmentsFromRawLines(b.lines)
    if (!segments.length) continue
    entries.push({ id: b.id, label: b.label, segments, sourceLines })
    segmentCount += segments.length
  }
  return {
    entries,
    hasAny: entries.length > 0,
    segmentCount
  }
}

/**
 * 仅从装备快照解析（每穿戴格一条目，与其它页区间代入一致）。
 */
export function estimateDamageConversionFromEquipment(
  equipment: Record<string, unknown> | null | undefined
): DamageConversionEquipmentEstimate {
  const empty: DamageConversionEquipmentEstimate = {
    entries: [],
    hasAny: false,
    segmentCount: 0
  }
  if (!equipment || typeof equipment !== 'object') return empty
  const equipped = equipment.equipped
  if (!Array.isArray(equipped)) return empty

  const bundles: DamageConversionSourceBundle[] = []
  for (let i = 0; i < equipped.length; i++) {
    if (equipped[i] == null) continue
    const lines = getResolvedEffectLinesForEquipmentSlot(equipment, i)
    if (!lines.length) continue
    bundles.push({
      id: `equipment-${i}`,
      label: `装备 · 槽位 ${i}`,
      lines: lines.map(String)
    })
  }

  const merged = estimateDamageConversionFromSourceBundles(bundles)
  return {
    entries: merged.entries.map(e => ({
      slotIndex: Number(String(e.id).replace(/^equipment-/, '')) || 0,
      segments: e.segments,
      sourceLines: e.sourceLines
    })),
    hasAny: merged.hasAny,
    segmentCount: merged.segmentCount
  }
}
