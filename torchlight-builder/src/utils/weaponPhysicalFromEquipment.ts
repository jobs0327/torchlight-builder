/**
 * 从 BD 装备快照中估算「攻击类技能」可用的 **物理点伤** 参考值（演示用）。
 *
 * - **攻击技能基础点伤（约定）**：**仅主手武器** — 武器白字 + 该装备附加物理，再乘本地 **% 该装备物理伤害**。**武器上的「攻击附加」** 不归入此基础，请在手填提高类或其它口径自行处理。**近战伤害 / 攻击伤害 / 通用 % 物理** 为提高类 inc，不并入本地乘区。
 * - **其他装备格**：仅汇总词条中的 **「主手武器附加 … 点物理伤害」**；不包含该装备附加、攻击和法术附加、攻击附加等（与主手武器段分开结算）。
 * - **双手武器（主手为双手近战）**：其它装备上的 **% 双手武器基础伤害**（排除「副手武器」类）**加总**后，乘在 **(白字+该装备附加)×(1+本地%该装备物理)** 这一段上，再与主手「主手武器附加」平加合并。
 * - **双持**：副手武器本地合计**仅作展示参考**，**不计入**本函数返回的 `totalPhysicalFlat`（攻击基础按主手单段）。
 *
 * 与游戏内真实结算可能不一致，仅用于计算器展示。
 */

import legendaryGearJson from '@/data/equipment/legendaryGear.json'
import { resolveEffectLineWithRollPicks } from '@/utils/effectLineRolls'

/** 与 Equipment.vue 中 EQUIPMENT_SLOTS 顺序一致 */
export const WEAPON_MAIN_SLOT_INDEX = 8
export const WEAPON_OFF_SLOT_INDEX = 9

/** 与 Equipment.vue TWO_HANDED_WEAPON_SLUGS 一致（近战双手） */
const TWO_HANDED_MELEE_SLUGS = new Set(['Two-Handed_Sword', 'Two-Handed_Hammer', 'Two-Handed_Axe'])
const SHIELD_SLUGS = new Set(['STR_Shield', 'DEX_Shield', 'INT_Shield'])

type LegendRow = { id: string; effectLines?: string[]; categories?: { slug: string }[] }

function buildLegendaryById(): Map<string, LegendRow> {
  const m = new Map<string, LegendRow>()
  const items = (legendaryGearJson as { items?: LegendRow[] }).items ?? []
  for (const it of items) {
    if (it?.id) m.set(it.id, it)
  }
  return m
}

const LEGENDARY_BY_ID = buildLegendaryById()

function norm(s: string): string {
  return s.replace(/[–—]/g, '-').trim()
}

/** 去掉装备页展示用的 `[基底]` / `[初阶前缀]` 等前缀，便于物理/攻速解析 */
function stripLeadingEffectLineTag(s: string): string {
  return norm(s).replace(/^\[[^\]]+\]\s*/, '')
}

function firstNumberMid(text: string): number | null {
  const s = norm(text)
  const range = s.match(/\(?([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\)?/)
  if (range) {
    const a = parseFloat(range[1]!)
    const b = parseFloat(range[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) return (a + b) / 2
  }
  const one = s.match(/([+-]?\d+(?:\.\d+)?)/)
  if (one) {
    const v = parseFloat(one[1]!)
    if (Number.isFinite(v)) return v
  }
  return null
}

function lastNumberMid(text: string): number | null {
  const s = norm(text)
  const tokens = [...s.matchAll(/\(?([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\)?|([+-]?\d+(?:\.\d+)?)/g)]
  if (!tokens.length) return null
  const t = tokens[tokens.length - 1]!
  if (t[1] != null && t[2] != null) {
    const a = parseFloat(t[1])
    const b = parseFloat(t[2])
    if (Number.isFinite(a) && Number.isFinite(b)) return (a + b) / 2
    return null
  }
  if (t[3] != null) {
    const v = parseFloat(t[3])
    return Number.isFinite(v) ? v : null
  }
  return null
}

/** 解析 (a-b) 或 (–a - -b) 形式区间的中值 */
function midFromParenRange(a: string, b: string): number | null {
  const x = parseFloat(a.replace(/[()]/g, ''))
  const y = parseFloat(b.replace(/[()]/g, ''))
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null
  return (x + y) / 2
}

/**
 * 匹配「(a-b) - (c-d) 点物理伤害」类双区间，返回 flat 中值。
 */
function parseDualRangePhysicalFlat(line: string): number | null {
  const s = norm(line)
  const m = s.match(
    /\(([-\d.]+)\s*-\s*([-\d.]+)\)\s*-\s*\(([-\d.]+)\s*-\s*([-\d.]+)\)\s*点物理伤害/
  )
  if (!m) return null
  const left = midFromParenRange(m[1]!, m[2]!)
  const right = midFromParenRange(m[3]!, m[4]!)
  if (left == null || right == null) return null
  return (left + right) / 2
}

/** 武器白字：行首「数字 - 数字 物理伤害」 */
function parseWeaponBasePhysicalLine(line: string): number | null {
  const s = norm(line)
  const m = s.match(/^(\d+(?:\.\d+)?)\s*-\s*(\d+(?:\.\d+)?)\s*物理伤害\s*$/)
  if (!m) return null
  const a = parseFloat(m[1]!)
  const b = parseFloat(m[2]!)
  if (!Number.isFinite(a) || !Number.isFinite(b)) return null
  return (a + b) / 2
}

/**
 * 该装备物理伤害：支持括号区间、多段 ± 数值（如高塔「+80 % 该装备物理伤害 -25 % 该装备物理伤害」）。
 */
function parseLocalIncPhysicalPctContributions(line: string): number {
  const s = norm(line)
  if (!s.includes('该装备物理伤害')) return 0
  let sum = 0
  const mParen = s.match(/\+?\(([-\d.]+)\s*-\s*([-\d.]+)\)\s*%\s*该装备物理伤害/)
  if (mParen) {
    const a = parseFloat(mParen[1]!)
    const b = parseFloat(mParen[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) sum += (a + b) / 2
  }
  const re = /([+-])(\d+(?:\.\d+)?)\s*%\s*该装备物理伤害/g
  let m: RegExpExecArray | null
  while ((m = re.exec(s)) !== null) {
    const sign = m[1] === '-' ? -1 : 1
    const v = parseFloat(m[2]!)
    if (Number.isFinite(v)) sum += sign * v
  }
  return sum
}

/** 该装备附加 … 点物理伤害（双括号区间，或「单数 - (a-b)」等变体） */
function parseGongzhuangAddedPhysical(line: string): number | null {
  const s = norm(line)
  if (!s.includes('该装备附加') || !s.endsWith('点物理伤害')) return null
  const dual = parseDualRangePhysicalFlat(s)
  if (dual != null) return dual
  // 代入装备页区间下拉后：该装备附加 8 - 15 点物理伤害（无双括号）
  const mPlain = s.match(
    /该装备附加\s+([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*点物理伤害\s*$/
  )
  if (mPlain) {
    const a = parseFloat(mPlain[1]!)
    const b = parseFloat(mPlain[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) return (a + b) / 2
  }
  // 例：该装备附加 4 - (5-7) 点物理伤害
  const m2 = s.match(
    /该装备附加\s+([+-]?\d+(?:\.\d+)?)\s*-\s*\(([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\)\s*点物理伤害\s*$/
  )
  if (m2) {
    const a = parseFloat(m2[1]!)
    const rMid = (parseFloat(m2[2]!) + parseFloat(m2[3]!)) / 2
    if (Number.isFinite(a) && Number.isFinite(rMid)) return (a + rMid) / 2
  }
  return null
}

/** 攻击附加 … 点物理伤害 */
function parseAttackAddedPhysical(line: string): number | null {
  const s = norm(line)
  if (!s.includes('攻击附加') || !s.endsWith('点物理伤害')) return null
  const dual = parseDualRangePhysicalFlat(s)
  if (dual != null) return dual
  const mPlain = s.match(
    /攻击附加\s+([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*点物理伤害\s*$/
  )
  if (mPlain) {
    const a = parseFloat(mPlain[1]!)
    const b = parseFloat(mPlain[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) return (a + b) / 2
  }
  return null
}

/** 与 Equipment.vue `equippedEffectsBlocks` 自制分支展示顺序、前缀一致，保证 effectRollSelections 的 key 对齐 */
const CRAFTED_AFFIX_TYPE_LABELS: { typeId: string; label: string }[] = [
  { typeId: '基础词缀', label: '基础词缀' },
  { typeId: '美梦词缀', label: '梦语词缀' },
  { typeId: '初阶前缀', label: '初阶前缀' },
  { typeId: '初阶后缀', label: '初阶后缀' },
  { typeId: '进阶前缀', label: '进阶前缀' },
  { typeId: '进阶后缀', label: '进阶后缀' },
  { typeId: '至臻前缀', label: '至臻前缀' },
  { typeId: '至臻后缀', label: '至臻后缀' }
]

function craftedAffixTypeDisplay(affixType: string): string {
  const hit = CRAFTED_AFFIX_TYPE_LABELS.find(x => x.typeId === affixType)
  return hit?.label ?? affixType
}

type CraftedAffixRow = { affixType?: string; effectPlain?: string }
type CraftedAffixRowFull = CraftedAffixRow & { modifierId?: string }

/** 与装备页「× 移除词条」元数据一致；行顺序与文案须与 `lines` 一一对应（影响区间选择 key） */
export type CraftedLineRemoveMetaEntry = {
  modifierId: string
  pool: 'craft' | 'basic' | 'dream' | 'tower'
}

/**
 * 自制装备：与左侧「已选效果」完全相同的展示行 + 移除元数据（单一数据源，避免与数据计算页行下标错位）。
 */
export function buildCraftedDisplayLinesAndRemoveMeta(o: Record<string, unknown>): {
  lines: string[]
  craftedLineRemoveMeta: Array<CraftedLineRemoveMetaEntry | null>
} {
  const lines: string[] = []
  const craftedLineRemoveMeta: Array<CraftedLineRemoveMetaEntry | null> = []
  if (Array.isArray(o.craftedBaseEffectLines)) {
    for (const x of o.craftedBaseEffectLines) {
      const t = String(x ?? '').trim()
      if (t) {
        lines.push(`[基底] ${t}`)
        craftedLineRemoveMeta.push(null)
      }
    }
  }
  const pushPool = (
    arr: unknown[],
    pool: CraftedLineRemoveMetaEntry['pool'],
    fmt: (row: CraftedAffixRowFull) => string
  ) => {
    if (!Array.isArray(arr)) return
    for (const a of arr) {
      if (!a || typeof a !== 'object') continue
      const row = a as CraftedAffixRowFull
      const plain = String(row.effectPlain ?? '').trim()
      if (!plain) continue
      lines.push(fmt(row))
      craftedLineRemoveMeta.push({ modifierId: String(row.modifierId ?? ''), pool })
    }
  }
  pushPool(o.craftedBasicAffixes as unknown[], 'basic', r =>
    `[${craftedAffixTypeDisplay(String(r.affixType ?? ''))}] ${String(r.effectPlain ?? '').trim()}`
  )
  pushPool(o.craftedDreamAffixes as unknown[], 'dream', r =>
    `[${craftedAffixTypeDisplay(String(r.affixType ?? ''))}] ${String(r.effectPlain ?? '').trim()}`
  )
  pushPool(o.craftedTowerSequenceAffixes as unknown[], 'tower', r => {
    const at = String(r.affixType ?? '')
    const tag = at === '高阶序列' ? '高塔序列·高阶' : '高塔序列·中阶'
    return `[${tag}] ${String(r.effectPlain ?? '').trim()}`
  })
  pushPool(o.craftedAffixes as unknown[], 'craft', r =>
    `[${craftedAffixTypeDisplay(String(r.affixType ?? ''))}] ${String(r.effectPlain ?? '').trim()}`
  )
  return { lines, craftedLineRemoveMeta }
}

/**
 * 与装备页一致：优先信 `kind`；旧快照或合并数据可能丢 `kind`，用 id / 自制字段兜底，避免误判为暗金查表导致词条为空。
 */
function itemIdStr(o: Record<string, unknown>): string {
  const raw = o.id
  if (raw == null) return ''
  return String(raw).trim()
}

function equippedLooksCrafted(o: Record<string, unknown>): boolean {
  if (o.kind === 'legendary') return false
  if (o.kind === 'crafted') return true
  const id = itemIdStr(o)
  if (id.startsWith('crafted-slot-')) return true
  const hasNonEmptyArr = (k: string) => {
    const v = o[k]
    return Array.isArray(v) && (v as unknown[]).length > 0
  }
  if (
    hasNonEmptyArr('craftedAffixes') ||
    hasNonEmptyArr('craftedBasicAffixes') ||
    hasNonEmptyArr('craftedDreamAffixes') ||
    hasNonEmptyArr('craftedTowerSequenceAffixes') ||
    hasNonEmptyArr('craftedBaseEffectLines')
  ) {
    return true
  }
  if (o.craftedGearBaseId != null && String(o.craftedGearBaseId).trim() !== '') return true
  const slug = o.craftedAffixCategorySlug
  if (typeof slug === 'string' && slug.trim() !== '') return true
  return false
}

/**
 * 与装备页「已选效果」列表相同的原始行（未代入区间下拉），用于再套 effectRollSelections。
 */
function buildDisplayEffectLinesForEquippedItem(o: Record<string, unknown>): string[] {
  if (equippedLooksCrafted(o)) {
    return buildCraftedDisplayLinesAndRemoveMeta(o).lines
  }

  const id = itemIdStr(o)
  if (!id) return []
  const hit = LEGENDARY_BY_ID.get(id)
  const arr = hit?.effectLines
  if (!Array.isArray(arr)) return []
  return arr.map(x => String(x).trim()).filter(Boolean)
}

function effectRollSelectionsMap(equipment: Record<string, unknown> | null | undefined): Record<string, string> {
  if (!equipment || typeof equipment !== 'object') return {}
  const raw = equipment.effectRollSelections
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return {}
  return raw as Record<string, string>
}

/** 代入装备模块已选区间后的词条行（与左侧「已选效果」+ 下拉一致） */
function collectResolvedLinesFromEquippedSlot(
  eq: unknown,
  slotIndex: number,
  equipment: Record<string, unknown> | null | undefined
): string[] {
  if (!eq || typeof eq !== 'object') return []
  const o = eq as Record<string, unknown>
  const selections = effectRollSelectionsMap(equipment)
  const itemId = itemIdStr(o)
  const displayLines = buildDisplayEffectLinesForEquippedItem(o)
  return displayLines.map((line, li) =>
    resolveEffectLineWithRollPicks(line, `${slotIndex}|${itemId}|${li}`, selections)
  )
}

/**
 * 非武器格：仅「主手武器附加 … 点物理伤害」（双区间中值），计入攻击技能基础点伤。
 */
function parseMainHandWeaponAddedPhysicalFlat(line: string): number | null {
  const s = norm(line)
  if (!s.includes('点物理伤害')) return null
  if (!/主手武器\s*附加/.test(s)) return null
  const dual = parseDualRangePhysicalFlat(s)
  if (dual != null) return dual
  const mPlain = s.match(
    /主手武器\s*附加\s+([+-]?\d+(?:\.\d+)?)\s*-\s*([+-]?\d+(?:\.\d+)?)\s*点物理伤害\s*$/
  )
  if (mPlain) {
    const a = parseFloat(mPlain[1]!)
    const b = parseFloat(mPlain[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) return (a + b) / 2
  }
  return null
}

/**
 * 其它来源上的「双手武器基础伤害」提高 %（如 额外 +(80–90) % 双手武器基础伤害）。
 * 不含副手武器专用词（避免与单手+盾副手词缀混淆）。
 */
function parseTwoHandedWeaponBaseDamageIncPct(line: string): number | null {
  const s = norm(line)
  if (/副手武器/.test(s)) return null
  if (!/双手武器/.test(s) || !s.includes('基础伤害')) return null
  if (!s.includes('%')) return null
  const i = s.indexOf('%')
  if (i <= 0) return null
  const before = s.slice(0, i)
  const v = firstNumberMid(before)
  return v != null && Number.isFinite(v) ? v : null
}

function parseAttackSpeedIncPct(line: string): number | null {
  const s = norm(line)
  if (!s.includes('攻击速度')) return null
  if (!s.includes('%')) return null
  const left = s.slice(0, s.indexOf('攻击速度'))
  return lastNumberMid(left)
}

function parseBaseAttackSpeed(line: string): number | null {
  const s = norm(line)
  const m = s.match(/^([+-]?\d+(?:\.\d+)?)\s*攻击速度$/)
  if (!m) return null
  const v = parseFloat(m[1]!)
  return Number.isFinite(v) ? v : null
}

/** 暴击词条归属：与当前技能类型（攻击/法术）过滤联用 */
export type CritValueScope = 'attack' | 'spell' | 'both'

export type CritContribution = {
  kind: 'pct' | 'flat'
  value: number
  scope: CritValueScope
}

function scopeForCritWindow(win: string): CritValueScope | null {
  if (win.includes('法术暴击值')) return 'spell'
  if (win.includes('攻击和法术暴击值')) return 'both'
  if (win.includes('攻击暴击值')) return 'attack'
  /** 须含「暴击值」，避免「暴击伤害」等误判 */
  if (win.includes('暴击值')) return 'both'
  return null
}

function parseCritPctContributions(s: string): CritContribution[] {
  const out: CritContribution[] = []
  const re = /([+-]?\d+(?:\.\d+)?)%/g
  let m: RegExpExecArray | null
  while ((m = re.exec(s)) !== null) {
    const n = parseFloat(m[1]!)
    if (!Number.isFinite(n)) continue
    const idx = m.index
    const win = s.slice(Math.max(0, idx - 32), Math.min(s.length, idx + m[0].length + 32))
    if (!/暴击/.test(win)) continue
    const scope = scopeForCritWindow(win)
    if (scope) out.push({ kind: 'pct', value: n, scope })
  }
  return out
}

function parseCritFlatContributions(s: string): CritContribution[] {
  const out: CritContribution[] = []
  if (s.includes('攻击和法术暴击值')) {
    const v = lastNumberMid(s.slice(0, s.lastIndexOf('攻击和法术暴击值')))
    if (v != null) out.push({ kind: 'flat', value: v, scope: 'both' })
    return out
  }
  if (s.includes('法术暴击值')) {
    const v = lastNumberMid(s.slice(0, s.lastIndexOf('法术暴击值')))
    if (v != null) out.push({ kind: 'flat', value: v, scope: 'spell' })
    return out
  }
  if (s.includes('攻击暴击值')) {
    const v = lastNumberMid(s.slice(0, s.lastIndexOf('攻击暴击值')))
    if (v != null) out.push({ kind: 'flat', value: v, scope: 'attack' })
    return out
  }
  if (s.includes('暴击值')) {
    const v = lastNumberMid(s.slice(0, s.lastIndexOf('暴击值')))
    if (v != null) out.push({ kind: 'flat', value: v, scope: 'both' })
  }
  return out
}

/**
 * 单条效果文案中的暴击值（% 或平），按关键词区分攻击 / 法术 / 双端。
 * 供装备、天赋、追忆及被动描述等复用。
 */
export function parseCritContributionsFromEffectLine(line: string): CritContribution[] {
  const s = norm(line)
  if (!s || !/暴击/.test(s)) return []
  if (!s.includes('%')) return parseCritFlatContributions(s)
  return parseCritPctContributions(s)
}

function legendaryItem(id: string): LegendRow | undefined {
  return LEGENDARY_BY_ID.get(id)
}

/** 与 Equipment.vue itemIsTwoHandedWeapon：仅三把双手近战 */
function isLegendaryTwoHandedMelee(id: string): boolean {
  const it = legendaryItem(id)
  return it?.categories?.some(c => TWO_HANDED_MELEE_SLUGS.has(c.slug)) ?? false
}

function isLegendaryShield(id: string): boolean {
  const it = legendaryItem(id)
  return it?.categories?.some(c => SHIELD_SLUGS.has(c.slug)) ?? false
}

function craftedSlug(eq: Record<string, unknown>): string {
  const w = eq.craftedWeaponCategorySlug ?? eq.craftedAffixCategorySlug
  return typeof w === 'string' ? w : ''
}

function isCraftedTwoHandedMelee(eq: Record<string, unknown>): boolean {
  const s = craftedSlug(eq)
  return s ? TWO_HANDED_MELEE_SLUGS.has(s) : false
}

function isCraftedShield(eq: Record<string, unknown>): boolean {
  const s = craftedSlug(eq)
  return s ? SHIELD_SLUGS.has(s) : false
}

/** 主手是否为双手近战（自制/暗金） */
export function equippedIsTwoHandedMeleeMain(eq: unknown): boolean {
  if (!eq || typeof eq !== 'object') return false
  const o = eq as Record<string, unknown>
  if (equippedLooksCrafted(o)) return isCraftedTwoHandedMelee(o)
  const id = itemIdStr(o)
  return id ? isLegendaryTwoHandedMelee(id) : false
}

/** 副手格是否为盾牌 */
function equippedIsShield(eq: unknown): boolean {
  if (!eq || typeof eq !== 'object') return false
  const o = eq as Record<string, unknown>
  if (equippedLooksCrafted(o)) return isCraftedShield(o)
  const id = itemIdStr(o)
  return id ? isLegendaryShield(id) : false
}

/** 副手格是否为「武器」（非盾、非空），用于双持判定 */
function equippedIsOffHandWeapon(eq: unknown): boolean {
  if (eq == null || typeof eq !== 'object') return false
  return !equippedIsShield(eq)
}

export type WeaponPhysicalEstimate = {
  /** 主手：白字物理中值 */
  weaponBaseAvg: number
  /** 主手：该装备附加物理 flat 之和（进入攻击基础） */
  weaponGongzhuangAddedSum: number
  /** 主手：攻击附加 flat（不计入攻击基础，见 notes） */
  weaponAttackAddedSum: number
  /** 主手：% 该装备物理伤害（取中值后加总） */
  weaponLocalIncPctSum: number
  /**
   * 主手：(白字+该装备附加)×(1+本地%该装备物理)；未乘其它装备上的「%双手武器基础伤害」。
   */
  weaponLocalAttackBase: number
  /** 非主手槽「% 双手武器基础伤害」加总（仅双手主手时参与计算，否则为 0） */
  otherSourcesTwoHandedBaseIncPctSum: number
  /**
   * 主手武器段合计：weaponLocalAttackBase×(1+otherSourcesTwoHandedBaseIncPctSum/100)（双手时）+ 主手「主手武器附加」平加。
   */
  weaponLocalTotal: number
  /** 副手：白字中值（双持展示） */
  offWeaponBaseAvg: number
  /** 副手：该装备附加之和 */
  offWeaponGongzhuangAddedSum: number
  /** 副手：攻击附加（展示，不计入 total） */
  offWeaponAttackAddedSum: number
  offWeaponLocalIncPctSum: number
  /** 副手本地攻击段（展示；不计入 totalPhysicalFlat） */
  offWeaponLocalTotal: number
  /** 主手是否为双手近战 */
  mainIsTwoHandedMelee: boolean
  /** 双持：单手主手且副手为武器 */
  dualWield: boolean
  /**
   * 与 `weaponLocalTotal` 相同：攻击技能武器段仅主手，双持时不与副手平均。
   */
  weaponStrikeAverage: number
  /** 其他部位「主手武器附加」物理 flat 之和 */
  otherSlotsMainHandWeaponFlatSum: number
  /** 各非武器槽「主手武器附加」贡献 */
  otherSlotsBySlot: { slotIndex: number; flatSum: number }[]
  /** 攻击技能基础物理点伤：主手武器段 + 其他格主手武器附加 */
  totalPhysicalFlat: number
  /** 简短说明（调试用） */
  notes: string[]
}

export type EquipmentAttackStatEstimate = {
  baseAttackPerSecond: number
  attackSpeedIncPct: number
  critValuePct: number
  critValueFlat: number
}

/** 装备上解析到的攻速/暴击词条明细（供数据计算页展示来源） */
export type EquipmentAttackStatSourceRow = {
  slotIndex: number
  snippet: string
  kind: 'baseAps' | 'attackSpeedInc' | 'critValuePct' | 'critValueFlat'
  value: number
  /** 仅暴击类；未写时视为双端 */
  critScope?: CritValueScope
}

export type EquipmentAttackStatDetail = EquipmentAttackStatEstimate & {
  sources: EquipmentAttackStatSourceRow[]
}

function effectLineSnippet(line: string, maxLen = 56): string {
  const t = norm(line)
  if (t.length <= maxLen) return t
  return `${t.slice(0, maxLen)}…`
}

function analyzeWeaponPhysicalLocal(lines: string[], label: string): {
  baseAvg: number
  gongzhuangAddedSum: number
  attackAddedSum: number
  incSum: number
  weaponLocalAttackBase: number
  notes: string[]
} {
  let baseAvg = 0
  let gongzhuangAddedSum = 0
  let attackAddedSum = 0
  let incSum = 0
  const notes: string[] = []
  let gotBase = false

  for (const raw of lines) {
    const line = stripLeadingEffectLineTag(raw)
    if (!line) continue

    const base = parseWeaponBasePhysicalLine(line)
    if (base != null && !gotBase) {
      baseAvg = base
      gotBase = true
      notes.push(`[${label}] 武器白字物理（中值）≈ ${baseAvg.toFixed(1)}`)
    }

    const incEquipPhys = parseLocalIncPhysicalPctContributions(line)
    if (incEquipPhys !== 0) {
      incSum += incEquipPhys
      notes.push(
        `[${label}] ${incEquipPhys >= 0 ? '+' : ''}${incEquipPhys.toFixed(1)}% 该装备物理伤害（本地 inc）`
      )
    }

    const add = parseGongzhuangAddedPhysical(line)
    if (add != null) {
      gongzhuangAddedSum += add
      notes.push(`[${label}] 该装备附加物理 ≈ ${add.toFixed(1)}（计入攻击基础）`)
    }

    const addAtk = parseAttackAddedPhysical(line)
    if (addAtk != null) {
      attackAddedSum += addAtk
      notes.push(
        `[${label}] 攻击附加物理 ≈ ${addAtk.toFixed(1)}（未计入攻击技能基础；请入手填提高/其它 flat）`
      )
    }
  }

  const weaponLocalAttackBase =
    (baseAvg + gongzhuangAddedSum) * (1 + Math.max(0, incSum) / 100)

  return { baseAvg, gongzhuangAddedSum, attackAddedSum, incSum, weaponLocalAttackBase, notes }
}

/** 武器/装备行中「主手武器附加」点伤之和（平加，不乘 % 该装备物理） */
function sumMainHandWeaponAddedFlatFromLines(lines: string[]): number {
  let sum = 0
  for (const raw of lines) {
    const line = stripLeadingEffectLineTag(raw)
    const v = parseMainHandWeaponAddedPhysicalFlat(line)
    if (v != null) sum += v
  }
  return sum
}

export function estimateAttackStatsFromEquipmentDetailed(
  equipment: Record<string, unknown> | null | undefined
): EquipmentAttackStatDetail {
  const empty: EquipmentAttackStatDetail = {
    baseAttackPerSecond: 0,
    attackSpeedIncPct: 0,
    critValuePct: 0,
    critValueFlat: 0,
    sources: []
  }
  if (!equipment || typeof equipment !== 'object') return empty
  const equipped = equipment.equipped
  if (!Array.isArray(equipped)) return empty

  let mainBaseAttack = 0
  let offBaseAttack = 0
  const main = equipped[WEAPON_MAIN_SLOT_INDEX]
  const mainIs2h = main && typeof main === 'object' ? equippedIsTwoHandedMeleeMain(main) : false
  const off = equipped[WEAPON_OFF_SLOT_INDEX]
  const dualWield =
    !!main &&
    typeof main === 'object' &&
    !mainIs2h &&
    !!off &&
    typeof off === 'object' &&
    equippedIsOffHandWeapon(off)

  let attackSpeedIncPct = 0
  let critValuePct = 0
  let critValueFlat = 0
  const sources: EquipmentAttackStatSourceRow[] = []

  for (let i = 0; i < equipped.length; i++) {
    const slot = equipped[i]
    if (slot == null) continue
    const lines = collectResolvedLinesFromEquippedSlot(slot, i, equipment)
    for (const raw of lines) {
      const line = stripLeadingEffectLineTag(raw)
      if (!line) continue
      const snip = effectLineSnippet(line)
      const baseAs = parseBaseAttackSpeed(line)
      if (baseAs != null) {
        if (i === WEAPON_MAIN_SLOT_INDEX) mainBaseAttack = baseAs
        else if (i === WEAPON_OFF_SLOT_INDEX) offBaseAttack = baseAs
        sources.push({ slotIndex: i, snippet: snip, kind: 'baseAps', value: baseAs })
      }
      const speed = parseAttackSpeedIncPct(line)
      if (speed != null) {
        attackSpeedIncPct += speed
        sources.push({ slotIndex: i, snippet: snip, kind: 'attackSpeedInc', value: speed })
      }
      for (const c of parseCritContributionsFromEffectLine(line)) {
        if (c.kind === 'pct') {
          critValuePct += c.value
          sources.push({
            slotIndex: i,
            snippet: snip,
            kind: 'critValuePct',
            value: c.value,
            critScope: c.scope
          })
        } else {
          critValueFlat += c.value
          sources.push({
            slotIndex: i,
            snippet: snip,
            kind: 'critValueFlat',
            value: c.value,
            critScope: c.scope
          })
        }
      }
    }
  }
  const baseAttackPerSecond =
    dualWield && offBaseAttack > 0
      ? (Math.max(0, mainBaseAttack) + Math.max(0, offBaseAttack)) / 2
      : Math.max(0, mainBaseAttack)
  return { baseAttackPerSecond, attackSpeedIncPct, critValuePct, critValueFlat, sources }
}

export function estimateAttackStatsFromEquipment(
  equipment: Record<string, unknown> | null | undefined
): EquipmentAttackStatEstimate {
  const d = estimateAttackStatsFromEquipmentDetailed(equipment)
  return {
    baseAttackPerSecond: d.baseAttackPerSecond,
    attackSpeedIncPct: d.attackSpeedIncPct,
    critValuePct: d.critValuePct,
    critValueFlat: d.critValueFlat
  }
}

/**
 * 从 build 快照里的 `equipment` 对象估算物理点伤。
 * 若 `equipped` 缺失或主手为空，返回 0 与说明。
 */
export function estimatePhysicalAttackFlatFromEquipment(
  equipment: Record<string, unknown> | null | undefined
): WeaponPhysicalEstimate {
  const notes: string[] = []
  const emptyBase = (): WeaponPhysicalEstimate => ({
    weaponBaseAvg: 0,
    weaponGongzhuangAddedSum: 0,
    weaponAttackAddedSum: 0,
    weaponLocalIncPctSum: 0,
    weaponLocalAttackBase: 0,
    otherSourcesTwoHandedBaseIncPctSum: 0,
    weaponLocalTotal: 0,
    offWeaponBaseAvg: 0,
    offWeaponGongzhuangAddedSum: 0,
    offWeaponAttackAddedSum: 0,
    offWeaponLocalIncPctSum: 0,
    offWeaponLocalTotal: 0,
    mainIsTwoHandedMelee: false,
    dualWield: false,
    weaponStrikeAverage: 0,
    otherSlotsMainHandWeaponFlatSum: 0,
    otherSlotsBySlot: [],
    totalPhysicalFlat: 0,
    notes: []
  })
  const empty: WeaponPhysicalEstimate = {
    ...emptyBase(),
    notes: ['未找到装备快照或主手为空']
  }

  if (!equipment || typeof equipment !== 'object') return empty

  const equipped = equipment.equipped
  if (!Array.isArray(equipped)) return empty

  const main = equipped[WEAPON_MAIN_SLOT_INDEX]
  if (main == null || typeof main !== 'object') {
    notes.push('主手武器格未装备')
    return { ...empty, notes }
  }

  const mainIs2h = equippedIsTwoHandedMeleeMain(main)
  const off = equipped[WEAPON_OFF_SLOT_INDEX]
  const dualWield =
    !mainIs2h && off != null && typeof off === 'object' && equippedIsOffHandWeapon(off)

  const mainLines = collectResolvedLinesFromEquippedSlot(main, WEAPON_MAIN_SLOT_INDEX, equipment)
  const mh = analyzeWeaponPhysicalLocal(mainLines, '主手')
  notes.push(...mh.notes)

  const mainHandWeaponAddedOnMain = sumMainHandWeaponAddedFlatFromLines(mainLines)
  if (mainHandWeaponAddedOnMain > 0) {
    notes.push(
      `[主手] 主手武器附加（平加，不乘本地%该装备）合计 ≈ ${mainHandWeaponAddedOnMain.toFixed(1)}`
    )
  }

  const weaponLocalAttackBase = mh.weaponLocalAttackBase
  let otherSourcesTwoHandedBaseIncPctSum = 0
  if (mainIs2h) {
    equipped.forEach((slot, idx) => {
      if (slot == null || idx === WEAPON_MAIN_SLOT_INDEX) return
      const lines = collectResolvedLinesFromEquippedSlot(slot, idx, equipment)
      for (const raw of lines) {
        const line = stripLeadingEffectLineTag(raw)
        const p = parseTwoHandedWeaponBaseDamageIncPct(line)
        if (p != null) {
          otherSourcesTwoHandedBaseIncPctSum += p
          notes.push(
            `[槽位 ${idx}] 双手武器基础伤害 ${p >= 0 ? '+' : ''}${p.toFixed(1)}%（${line.slice(0, 42)}…）`
          )
        }
      }
    })
    if (otherSourcesTwoHandedBaseIncPctSum !== 0) {
      notes.push(
        `双手武器：其它装备「%双手武器基础伤害」合计 ${otherSourcesTwoHandedBaseIncPctSum >= 0 ? '+' : ''}${otherSourcesTwoHandedBaseIncPctSum.toFixed(1)}%，已乘在 (白字+该装备附加)×本地 inc 段上`
      )
    }
  }

  const weaponLocalTotal =
    weaponLocalAttackBase * (1 + otherSourcesTwoHandedBaseIncPctSum / 100) + mainHandWeaponAddedOnMain

  let offWeaponBaseAvg = 0
  let offWeaponGongzhuangAddedSum = 0
  let offWeaponAttackAddedSum = 0
  let offWeaponLocalIncPctSum = 0
  let offWeaponLocalTotal = 0

  if (dualWield) {
    const offLines = collectResolvedLinesFromEquippedSlot(off, WEAPON_OFF_SLOT_INDEX, equipment)
    const oh = analyzeWeaponPhysicalLocal(offLines, '副手')
    notes.push(...oh.notes)
    offWeaponBaseAvg = oh.baseAvg
    offWeaponGongzhuangAddedSum = oh.gongzhuangAddedSum
    offWeaponAttackAddedSum = oh.attackAddedSum
    offWeaponLocalIncPctSum = oh.incSum
    offWeaponLocalTotal = oh.weaponLocalAttackBase
    notes.push(
      `双持：攻击技能基础仅计主手武器段 ${weaponLocalTotal.toFixed(1)}；副手本地 ${offWeaponLocalTotal.toFixed(1)} 未计入 totalPhysicalFlat。`
    )
  }

  const weaponStrikeAverage = weaponLocalTotal

  let otherSlotsMainHandWeaponFlatSum = 0
  const otherSlotsBySlot: { slotIndex: number; flatSum: number }[] = []
  const perSlotFlat = new Map<number, number>()

  equipped.forEach((slot, idx) => {
    if (slot == null) return
    if (idx === WEAPON_MAIN_SLOT_INDEX) return

    const lines = collectResolvedLinesFromEquippedSlot(slot, idx, equipment)
    // 双持副手格：只扫「主手武器附加」（武器本地白字/该装备附加已在 offWeaponLocalTotal 展示，不计入 total）
    if (dualWield && idx === WEAPON_OFF_SLOT_INDEX) {
      for (const raw of lines) {
        const line = stripLeadingEffectLineTag(raw)
        const v = parseMainHandWeaponAddedPhysicalFlat(line)
        if (v != null) {
          otherSlotsMainHandWeaponFlatSum += v
          perSlotFlat.set(idx, (perSlotFlat.get(idx) ?? 0) + v)
          notes.push(`[副手] 主手武器附加物理 ≈ ${v.toFixed(1)}（${line.slice(0, 40)}…）`)
        }
      }
      return
    }

    for (const raw of lines) {
      const line = stripLeadingEffectLineTag(raw)
      const v = parseMainHandWeaponAddedPhysicalFlat(line)
      if (v != null) {
        otherSlotsMainHandWeaponFlatSum += v
        perSlotFlat.set(idx, (perSlotFlat.get(idx) ?? 0) + v)
        notes.push(`[槽位 ${idx}] 主手武器附加物理 ≈ ${v.toFixed(1)}（${line.slice(0, 40)}…）`)
      }
    }
  })

  for (const [slotIndex, flatSum] of [...perSlotFlat.entries()].sort((a, b) => a[0] - b[0])) {
    if (flatSum > 0) otherSlotsBySlot.push({ slotIndex, flatSum })
  }

  const totalPhysicalFlat = weaponStrikeAverage + otherSlotsMainHandWeaponFlatSum

  return {
    weaponBaseAvg: mh.baseAvg,
    weaponGongzhuangAddedSum: mh.gongzhuangAddedSum,
    weaponAttackAddedSum: mh.attackAddedSum,
    weaponLocalIncPctSum: mh.incSum,
    weaponLocalAttackBase,
    otherSourcesTwoHandedBaseIncPctSum,
    weaponLocalTotal,
    offWeaponBaseAvg,
    offWeaponGongzhuangAddedSum,
    offWeaponAttackAddedSum,
    offWeaponLocalIncPctSum,
    offWeaponLocalTotal,
    mainIsTwoHandedMelee: mainIs2h,
    dualWield,
    weaponStrikeAverage,
    otherSlotsMainHandWeaponFlatSum,
    otherSlotsBySlot,
    totalPhysicalFlat,
    notes
  }
}

/**
 * 单格装备的「已选效果」文案（已代入区间下拉），与装备模块左侧列表一致；供 BuildCalc 预览等。
 */
export function getResolvedEffectLinesForEquipmentSlot(
  equipment: Record<string, unknown> | null | undefined,
  slotIndex: number
): string[] {
  if (!equipment || typeof equipment !== 'object') return []
  const equipped = equipment.equipped
  if (!Array.isArray(equipped) || slotIndex < 0 || slotIndex >= equipped.length) return []
  const cell = equipped[slotIndex]
  return collectResolvedLinesFromEquippedSlot(cell, slotIndex, equipment)
}

// ——————————————————————————————————————————————————————————————————————
// 主属性（力量 / 敏捷 / 智慧）平值：从装备已选效果粗算，供「每点力量」类天赋展示用
// ——————————————————————————————————————————————————————————————————————

export type PrimaryStatKind = '力量' | '敏捷' | '智慧'

function parseFlatPrimaryAttributeLine(line: string, kind: PrimaryStatKind): number {
  const s = norm(line).replace(/\s+/g, '')
  if (!s.includes(kind)) return 0
  let sum = 0
  let m: RegExpExecArray | null
  const rePlus = new RegExp(`[+＋](\\d+(?:\\.\\d+)?)${kind}`, 'g')
  while ((m = rePlus.exec(s)) !== null) {
    const n = parseFloat(m[1]!)
    if (Number.isFinite(n)) sum += n
  }
  const rePoint = new RegExp(`(\\d+(?:\\.\\d+)?)点${kind}`, 'g')
  while ((m = rePoint.exec(s)) !== null) {
    const n = parseFloat(m[1]!)
    if (Number.isFinite(n)) sum += n
  }
  const reAfter = new RegExp(`${kind}[+＋](\\d+(?:\\.\\d+)?)`, 'g')
  while ((m = reAfter.exec(s)) !== null) {
    const n = parseFloat(m[1]!)
    if (Number.isFinite(n)) sum += n
  }
  const reRange = new RegExp(`\\((\\d+(?:\\.\\d+)?)-(\\d+(?:\\.\\d+)?)\\)${kind}`, 'g')
  while ((m = reRange.exec(s)) !== null) {
    const a = parseFloat(m[1]!)
    const b = parseFloat(m[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) sum += (a + b) / 2
  }
  return sum
}

/**
 * 汇总装备各格「已选效果」中与主属性相关的 **平加** 文案（演示粗算，不含天赋/追忆/等级）。
 */
export function estimatePrimaryStatFlatFromEquipment(
  equipment: Record<string, unknown> | null | undefined,
  kind: PrimaryStatKind
): number {
  if (!equipment || typeof equipment !== 'object') return 0
  const equipped = equipment.equipped
  if (!Array.isArray(equipped)) return 0
  let sum = 0
  for (let i = 0; i < equipped.length; i++) {
    const lines = collectResolvedLinesFromEquippedSlot(equipped[i], i, equipment)
    for (const raw of lines) {
      const line = stripLeadingEffectLineTag(raw)
      sum += parseFlatPrimaryAttributeLine(line, kind)
    }
  }
  return sum
}
