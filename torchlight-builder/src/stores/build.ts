import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'torchlight:build:v1:current'
const STORAGE_KEY_EQUIPMENT = 'torchlight:build:v1:equipment'
const STORAGE_VERSION = 1

/** 与 Equipment.vue 槽位数量一致 */
const EQUIPMENT_EQUIPPED_SLOT_COUNT = 10

function hasTenSlotEquippedArray(eq: unknown): boolean {
  if (!eq || typeof eq !== 'object' || Array.isArray(eq)) return false
  const arr = (eq as Record<string, unknown>).equipped
  return Array.isArray(arr) && arr.length === EQUIPMENT_EQUIPPED_SLOT_COUNT
}

/** 已穿装备格数量（非 null）；用于 hydrate 时禁止「全空兜底」覆盖主快照里仍有装备的构筑 */
function equippedNonNullCount(eq: unknown): number {
  if (!hasTenSlotEquippedArray(eq)) return 0
  const arr = (eq as Record<string, unknown>).equipped as unknown[]
  return arr.reduce<number>((n, x) => n + (x != null ? 1 : 0), 0)
}

function equipmentSavedAt(eq: unknown): number {
  if (!eq || typeof eq !== 'object' || Array.isArray(eq)) return 0
  const v = (eq as Record<string, unknown>).savedAt
  return typeof v === 'number' && Number.isFinite(v) ? v : 0
}

/**
 * 主快照与 `torchlight:build:v1:equipment` 合并：绝不用「更少已穿格」的装备数据覆盖更满的一方，
 * 避免 persist 写入的全空格快照在刷新后覆盖当前 BD 里仍有装备的数据（数据计算全 0）。
 */
function mergeEquipmentFromHydrate(
  mainEquipment: unknown,
  fallbackRaw: unknown
): Record<string, unknown> {
  const mainOk = hasTenSlotEquippedArray(mainEquipment)
  const fbOk = hasTenSlotEquippedArray(fallbackRaw)

  if (!mainOk && !fbOk) {
    return mainEquipment && typeof mainEquipment === 'object' && !Array.isArray(mainEquipment)
      ? toJsonSafe(mainEquipment as Record<string, unknown>)
      : {}
  }
  if (!mainOk && fbOk) {
    return toJsonSafe(fallbackRaw as Record<string, unknown>)
  }
  if (mainOk && !fbOk) {
    return toJsonSafe(mainEquipment as Record<string, unknown>)
  }

  const mainCount = equippedNonNullCount(mainEquipment)
  const fbCount = equippedNonNullCount(fallbackRaw)
  if (fbCount > mainCount) {
    return toJsonSafe(fallbackRaw as Record<string, unknown>)
  }
  if (mainCount > fbCount) {
    return toJsonSafe(mainEquipment as Record<string, unknown>)
  }

  // 已穿格数相同（含同为 0）：较新 savedAt 优先，便于区间选择与清空状态跟装备页一致
  const mainSa = equipmentSavedAt(mainEquipment)
  const fbSa = equipmentSavedAt(fallbackRaw)
  const pick = fbSa > mainSa ? fallbackRaw : mainEquipment
  return toJsonSafe(pick as Record<string, unknown>)
}

export type MemorySelectionItem = {
  modifierId?: string | null
  /** 代入范围取值后的展示/计算用文案 */
  effectText: string
  /** 含 (a–b) 多段范围时的原始模板，与 rangePicks 顺序对应 */
  effectTextRaw?: string | null
  /** 各 (min–max) 段选中的整数值，默认取区间中值 */
  rangePicks?: number[] | null
  sourceId: string
  sourceName: string
  sourcePath: string
  category: string
  tier?: number | null
  tierLabel?: string
  level?: number | null
  weight?: number | null
  memoryRarity?: string | null
}

/** 与 hero_memories.json items.id 一致：本源 / 守己 / 奋进 各一套词条 */
export const MEMORY_ITEM_SOURCE_IDS = [
  'Memory_of_Origin',
  'Memory_of_Discipline',
  'Memory_of_Progress'
] as const

export type MemoryPerSourceSelections = {
  base: MemorySelectionItem | null
  implicit: MemorySelectionItem[]
  random: MemorySelectionItem[]
}

export type MemoriesSnapshot = {
  /** 每种追忆物品独立：各 1 基础 + 最多 2 固有 + 最多 2 随机 */
  perSource: Record<string, MemoryPerSourceSelections>
}

export function createEmptyPerSourceRecord(): Record<string, MemoryPerSourceSelections> {
  const empty = (): MemoryPerSourceSelections => ({
    base: null,
    implicit: [],
    random: []
  })
  const o: Record<string, MemoryPerSourceSelections> = {}
  for (const id of MEMORY_ITEM_SOURCE_IDS) {
    o[id] = empty()
  }
  return o
}

/** 汇总展示 / 统计用 */
export function flattenMemories(m: MemoriesSnapshot | undefined | null): {
  bases: MemorySelectionItem[]
  implicit: MemorySelectionItem[]
  random: MemorySelectionItem[]
} {
  const bases: MemorySelectionItem[] = []
  const implicit: MemorySelectionItem[] = []
  const random: MemorySelectionItem[] = []
  const ps = m?.perSource
  if (!ps || typeof ps !== 'object') {
    return { bases, implicit, random }
  }
  for (const cell of Object.values(ps)) {
    if (!cell || typeof cell !== 'object') continue
    if (cell.base) bases.push(cell.base)
    if (Array.isArray(cell.implicit)) implicit.push(...cell.implicit)
    if (Array.isArray(cell.random)) random.push(...cell.random)
  }
  return { bases, implicit, random }
}

function normalizeMemories(raw: unknown): MemoriesSnapshot {
  const defaults = createEmptyPerSourceRecord()

  const sliceCell = (cell: unknown): MemoryPerSourceSelections | null => {
    if (!cell || typeof cell !== 'object' || Array.isArray(cell)) return null
    const c = cell as Record<string, unknown>
    const base =
      c.base != null && typeof c.base === 'object' && !Array.isArray(c.base)
        ? (c.base as MemorySelectionItem)
        : null
    const implicit = Array.isArray(c.implicit) ? (c.implicit as MemorySelectionItem[]).slice(0, 2) : []
    const random = Array.isArray(c.random) ? (c.random as MemorySelectionItem[]).slice(0, 2) : []
    return { base, implicit, random }
  }

  if (raw && typeof raw === 'object' && !Array.isArray(raw)) {
    const r = raw as Record<string, unknown>
    if (r.perSource && typeof r.perSource === 'object' && !Array.isArray(r.perSource)) {
      const ps = r.perSource as Record<string, unknown>
      const merged = createEmptyPerSourceRecord()
      for (const id of MEMORY_ITEM_SOURCE_IDS) {
        const parsed = sliceCell(ps[id])
        if (parsed) merged[id] = parsed
      }
      for (const [id, cell] of Object.entries(ps)) {
        if ((MEMORY_ITEM_SOURCE_IDS as readonly string[]).includes(id)) continue
        const parsed = sliceCell(cell)
        if (parsed) merged[id] = parsed
      }
      return { perSource: merged }
    }

    // 旧版：全局 1 基础 + 共用 2 固有 + 2 随机 → 按词条 sourceId 拆回三种追忆
    const merged = createEmptyPerSourceRecord()
    const legacyBase = r.base
    if (legacyBase != null && typeof legacyBase === 'object' && !Array.isArray(legacyBase)) {
      const b = legacyBase as MemorySelectionItem
      const sid = String(b.sourceId ?? '').trim()
      const bucket = sid && merged[sid] ? sid : MEMORY_ITEM_SOURCE_IDS[0]
      merged[bucket] = { ...merged[bucket]!, base: b }
    }
    const legacyImplicit = Array.isArray(r.implicit) ? (r.implicit as MemorySelectionItem[]) : []
    for (const row of legacyImplicit) {
      const sid = String(row.sourceId ?? '').trim()
      const bucket = sid && merged[sid] ? sid : MEMORY_ITEM_SOURCE_IDS[0]
      const cell = merged[bucket]!
      if (cell.implicit.length < 2) cell.implicit = [...cell.implicit, row]
    }
    const legacyRandom = Array.isArray(r.random) ? (r.random as MemorySelectionItem[]) : []
    for (const row of legacyRandom) {
      const sid = String(row.sourceId ?? '').trim()
      const bucket = sid && merged[sid] ? sid : MEMORY_ITEM_SOURCE_IDS[0]
      const cell = merged[bucket]!
      if (cell.random.length < 2) cell.random = [...cell.random, row]
    }
    return { perSource: merged }
  }

  return { perSource: defaults }
}

export type BuildSnapshot = {
  version: number
  updatedAt: number
  hero: Record<string, unknown>
  talent: {
    nodeIds: string[]
    profession: {
      treeId: string
      allocatedPoints: number
      selected: boolean
    }[]
    /** 职业天赋树完整状态（用于刷新后恢复） */
    professionTreesFull?: unknown
  }
  skills: Record<string, unknown>
  memories: MemoriesSnapshot
  equipment: Record<string, unknown>
  pactspirit: Record<string, unknown>
}

function createDefaultSnapshot(): BuildSnapshot {
  return {
    version: STORAGE_VERSION,
    updatedAt: Date.now(),
    hero: {},
    talent: {
      nodeIds: [],
      profession: []
    },
    skills: {},
    memories: normalizeMemories(null),
    equipment: {},
    pactspirit: {}
  }
}

function toJsonSafe<T>(value: T): T {
  return JSON.parse(JSON.stringify(value)) as T
}

export const useBuildStore = defineStore('build', () => {
  const snapshot = ref<BuildSnapshot>(createDefaultSnapshot())

  function hydrate() {
    const base = createDefaultSnapshot()
    let merged: BuildSnapshot = base
    try {
      const raw = localStorage.getItem(STORAGE_KEY)
      if (raw) {
        const parsed = JSON.parse(raw) as Partial<BuildSnapshot>
        if (parsed && parsed.version === STORAGE_VERSION) {
          merged = {
            ...base,
            ...parsed,
            updatedAt: Date.now()
          }
          merged.memories = normalizeMemories(merged.memories)
        }
      }
    } catch {
      // ignore invalid persisted payload
    }
    // 装备：与独立 key 按「已穿格数 + savedAt」合并，避免全空格快照覆盖仍有装备的 BD。
    try {
      const rawEq = localStorage.getItem(STORAGE_KEY_EQUIPMENT)
      if (rawEq) {
        const eq = JSON.parse(rawEq) as unknown
        merged.equipment = mergeEquipmentFromHydrate(merged.equipment, eq)
      }
    } catch {
      // ignore invalid equipment fallback payload
    }
    snapshot.value = merged
  }

  /**
   * 写入 localStorage 时**不要**再改 snapshot 上的字段，否则 deep watch(snapshot) 会再次触发，
   * 形成反复 persist（极端情况下可能导致异常或写入不稳定）。
   */
  function persist() {
    const payload: BuildSnapshot = {
      ...snapshot.value,
      updatedAt: Date.now()
    }
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(payload))
      try {
        localStorage.setItem(STORAGE_KEY_EQUIPMENT, JSON.stringify(payload.equipment ?? {}))
      } catch {
        // ignore equipment fallback write failure
      }
      return
    } catch (err) {
      // 常见于 localStorage 容量超限；降级去掉超重字段重试，保证核心构筑数据（含装备）可持久化。
      const compact: BuildSnapshot = {
        ...payload,
        talent: {
          ...payload.talent,
          professionTreesFull: undefined
        }
      }
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(compact))
        try {
          localStorage.setItem(STORAGE_KEY_EQUIPMENT, JSON.stringify(compact.equipment ?? {}))
        } catch {
          // ignore equipment fallback write failure
        }
        return
      } catch (err2) {
        console.warn('[buildStore] persist failed', err, err2)
      }
    }
  }

  function resetAll() {
    snapshot.value = createDefaultSnapshot()
    persist()
    try {
      localStorage.removeItem(STORAGE_KEY_EQUIPMENT)
    } catch {
      // ignore remove failure
    }
  }

  function setHero(data: Record<string, unknown>) {
    snapshot.value.hero = toJsonSafe(data)
  }

  function setTalent(data: BuildSnapshot['talent']) {
    snapshot.value.talent = toJsonSafe(data)
  }

  function setSkills(data: Record<string, unknown>) {
    snapshot.value.skills = toJsonSafe(data)
  }

  function setEquipment(data: Record<string, unknown>) {
    snapshot.value.equipment = toJsonSafe(data)
  }

  function setPactspirit(data: Record<string, unknown>) {
    snapshot.value.pactspirit = toJsonSafe(data)
  }

  function setMemorySelectionsPerSource(perSource: Record<string, MemoryPerSourceSelections>) {
    const next = createEmptyPerSourceRecord()
    for (const id of MEMORY_ITEM_SOURCE_IDS) {
      const cell = perSource[id]
      if (cell) {
        next[id] = {
          base: toJsonSafe(cell.base),
          implicit: toJsonSafe(cell.implicit ?? []).slice(0, 2),
          random: toJsonSafe(cell.random ?? []).slice(0, 2)
        }
      }
    }
    for (const [id, cell] of Object.entries(perSource)) {
      if ((MEMORY_ITEM_SOURCE_IDS as readonly string[]).includes(id)) continue
      if (cell) {
        next[id] = {
          base: toJsonSafe(cell.base),
          implicit: toJsonSafe(cell.implicit ?? []).slice(0, 2),
          random: toJsonSafe(cell.random ?? []).slice(0, 2)
        }
      }
    }
    snapshot.value.memories = { perSource: next }
    snapshot.value.updatedAt = Date.now()
  }

  hydrate()
  watch(snapshot, persist, { deep: true })

  return {
    snapshot,
    resetAll,
    setHero,
    setTalent,
    setSkills,
    setEquipment,
    setPactspirit,
    setMemorySelectionsPerSource
  }
})

