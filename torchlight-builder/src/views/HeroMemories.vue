<template>
  <div class="hm-page">
    <div class="hm-sidebar">
      <div class="hm-sidebar-head">
        <h2>英雄追忆</h2>
        <span class="hm-count">{{ affixes.length }}</span>
      </div>

      <div class="hm-items" role="list">
        <button
          v-for="it in items"
          :key="it.id"
          type="button"
          class="hm-item-card hm-item-memory"
          :class="{ active: sourceFilter === it.id }"
          @click="sourceFilter = it.id"
        >
          <span class="hm-item-icon-wrap">
            <img v-if="it.iconUrl" :src="it.iconUrl" class="hm-item-icon" alt="" />
          </span>
          <span class="hm-item-text">
            <span class="hm-item-name">{{ it.name }}</span>
          </span>
        </button>
        <button
          type="button"
          class="hm-item-card hm-item-all"
          :class="{ active: sourceFilter === 'all' }"
          @click="sourceFilter = 'all'"
        >
          <span class="hm-item-text">
            <span class="hm-item-name">全部来源</span>
            <span class="hm-item-sub">词缀总表</span>
          </span>
        </button>
      </div>

      <div class="hm-filters" role="tablist" aria-label="词缀类型">
        <button
          v-for="tab in categoryTabs"
          :key="tab.id"
          type="button"
          class="hm-filter-tab"
          role="tab"
          :class="{ active: categoryFilter === tab.id }"
          @click="categoryFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      <div
        v-if="categoryFilter !== '基础属性'"
        class="hm-filters"
        role="tablist"
        aria-label="词条Tier"
      >
        <button
          v-for="tab in tierTabsForFilter"
          :key="tab.id"
          type="button"
          class="hm-filter-tab"
          role="tab"
          :class="{ active: tierFilter === tab.id }"
          @click="tierFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>

      <div class="hm-search">
        <input
          v-model="query"
          type="search"
          class="hm-search-input"
          placeholder="搜索词缀效果…"
          autocomplete="off"
          spellcheck="false"
        />
      </div>

      <div class="hm-picked">
        <div class="hm-picked-title">已选属性</div>
        <p class="hm-picked-hint">
          点击表格行选择；<strong>本源、守己、奋进</strong>三种追忆各自独立：每种各 1 条基础，固有 / 随机各最多 2 条。含数值范围的词条在文案中直接嵌入下拉选择，默认区间中值。
        </p>

        <p class="hm-picked-global">
          <template v-for="(it, idx) in items" :key="it.id">
            <span v-if="idx > 0" class="hm-picked-dot">·</span>
            <span class="hm-picked-mem-quota"
              >{{ memoryShortLabel(it.name) }} 基础 {{ quotaFor(it.id).base }}/1 固有
              {{ quotaFor(it.id).implicit }}/2 随机 {{ quotaFor(it.id).random }}/2</span
            >
          </template>
        </p>

        <div class="hm-picked-by-mem">
          <div class="hm-picked-subtitle">按追忆统计</div>
          <div v-for="block in pickedByMemory" :key="block.id" class="hm-mem-block">
            <div class="hm-mem-head">
              <span class="hm-mem-name">{{ block.name }}</span>
              <span class="hm-mem-total">共 {{ block.total }} 条</span>
            </div>
            <ul class="hm-mem-list" role="list">
              <li class="hm-mem-line">
                <span class="hm-mem-k">基础</span>
                <span class="hm-mem-n">{{ block.countBase }} 条</span>
                <span class="hm-mem-v">
                  <template v-if="block.base">
                    <div class="hm-mem-inline-entry" @click.stop>
                      <span class="hm-inline-fx">
                        <template
                          v-for="(seg, si) in memoryEffectInlineSegments(block.base)"
                          :key="`b-${si}`"
                        >
                          <span v-if="seg.type === 'text'" class="hm-inline-txt">{{ seg.value }}</span>
                          <select
                            v-else
                            class="hm-inline-sel"
                            :value="String(seg.current)"
                            @change="
                              onMemoryRangeChange(
                                block.id,
                                'base',
                                0,
                                seg.rangeIndex,
                                ($event.target as HTMLSelectElement).value
                              )
                            "
                          >
                            <option v-for="opt in seg.options" :key="opt" :value="String(opt)">{{
                              opt
                            }}</option>
                          </select>
                        </template>
                      </span>
                    </div>
                  </template>
                  <template v-else>—</template>
                </span>
              </li>
              <li class="hm-mem-line">
                <span class="hm-mem-k">固有</span>
                <span class="hm-mem-n">{{ block.implicit.length }} 条</span>
                <span class="hm-mem-v">
                  <template v-if="block.implicit.length">
                    <div
                      v-for="(r, i) in block.implicit"
                      :key="`im-${affixKey(r)}-${i}`"
                      class="hm-mem-inline-entry hm-mem-inline-entry--list"
                      @click.stop
                    >
                      <span v-if="r.tierLabel" class="hm-inline-tier">{{ r.tierLabel }}</span>
                      <span class="hm-inline-fx">
                        <template
                          v-for="(seg, si) in memoryEffectInlineSegments(r)"
                          :key="`im-${i}-${si}`"
                        >
                          <span v-if="seg.type === 'text'" class="hm-inline-txt">{{ seg.value }}</span>
                          <select
                            v-else
                            class="hm-inline-sel"
                            :value="String(seg.current)"
                            @change="
                              onMemoryRangeChange(
                                block.id,
                                'implicit',
                                i,
                                seg.rangeIndex,
                                ($event.target as HTMLSelectElement).value
                              )
                            "
                          >
                            <option v-for="opt in seg.options" :key="opt" :value="String(opt)">{{
                              opt
                            }}</option>
                          </select>
                        </template>
                      </span>
                    </div>
                  </template>
                  <template v-else>—</template>
                </span>
              </li>
              <li class="hm-mem-line">
                <span class="hm-mem-k">随机</span>
                <span class="hm-mem-n">{{ block.random.length }} 条</span>
                <span class="hm-mem-v">
                  <template v-if="block.random.length">
                    <div
                      v-for="(r, i) in block.random"
                      :key="`rn-${affixKey(r)}-${i}`"
                      class="hm-mem-inline-entry hm-mem-inline-entry--list"
                      @click.stop
                    >
                      <span v-if="r.tierLabel" class="hm-inline-tier">{{ r.tierLabel }}</span>
                      <span class="hm-inline-fx">
                        <template
                          v-for="(seg, si) in memoryEffectInlineSegments(r)"
                          :key="`rn-${i}-${si}`"
                        >
                          <span v-if="seg.type === 'text'" class="hm-inline-txt">{{ seg.value }}</span>
                          <select
                            v-else
                            class="hm-inline-sel"
                            :value="String(seg.current)"
                            @change="
                              onMemoryRangeChange(
                                block.id,
                                'random',
                                i,
                                seg.rangeIndex,
                                ($event.target as HTMLSelectElement).value
                              )
                            "
                          >
                            <option v-for="opt in seg.options" :key="opt" :value="String(opt)">{{
                              opt
                            }}</option>
                          </select>
                        </template>
                      </span>
                    </div>
                  </template>
                  <template v-else>—</template>
                </span>
              </li>
            </ul>
          </div>
        </div>

      </div>
    </div>

    <div class="hm-main">
      <div class="hm-table-wrap">
        <table class="hm-table">
          <thead>
            <tr>
              <th class="hm-col-effect">词缀效果</th>
              <th class="hm-col-source">来源</th>
              <th class="hm-col-cat">类型</th>
              <th v-if="showTierColumn" class="hm-col-tier">Tier</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="(row, i) in filteredAffixes"
              :key="`${row.modifierId ?? 'x'}-${i}`"
              class="hm-data-row"
              :class="{ 'hm-row-selected': isRowSelected(row) }"
              role="button"
              tabindex="0"
              @click="toggleSelect(row)"
              @keydown.enter.prevent="toggleSelect(row)"
              @keydown.space.prevent="toggleSelect(row)"
            >
              <td class="hm-col-effect">{{ row.effectText }}</td>
              <td class="hm-col-source">
                <a
                  :href="tlidbUrl(row.sourcePath)"
                  target="_blank"
                  rel="noopener noreferrer"
                  @click.stop
                >{{ row.sourceName }}</a>
              </td>
              <td class="hm-col-cat">{{ row.category }}</td>
              <td v-if="showTierColumn" class="hm-col-tier">{{ tierCellText(row) }}</td>
            </tr>
          </tbody>
        </table>
        <p v-if="filteredAffixes.length === 0" class="hm-empty">无匹配词缀</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import heroMemoriesJson from '@/data/hero_memories.json'
import {
  useBuildStore,
  type MemoryPerSourceSelections,
  type MemorySelectionItem,
  createEmptyPerSourceRecord,
  MEMORY_ITEM_SOURCE_IDS
} from '@/stores/build'
import {
  memoryEffectInlineSegments,
  normalizeMemorySelectionItem,
  patchMemoryItemRangePick
} from '@/utils/memoryEffectRoll'

type MemoryItem = {
  id: string
  name: string
  detailPath: string
  iconUrl?: string
  cdnIconUrl?: string
}

type AffixRow = {
  modifierId?: string | null
  effectText: string
  sourceId: string
  sourceName: string
  sourcePath: string
  category: string
  tier?: number | null
  tierLabel?: string
  level?: number | null
  weight?: number | null
  memoryRarity?: string
}

const payload = heroMemoriesJson as {
  items?: MemoryItem[]
  affixes?: AffixRow[]
}

const items = payload.items ?? []
const affixes = payload.affixes ?? []
const buildStore = useBuildStore()

const perSource = ref<Record<string, MemoryPerSourceSelections>>(createEmptyPerSourceRecord())

function cloneCell(cell: MemoryPerSourceSelections): MemoryPerSourceSelections {
  return {
    base: cell.base ? normalizeMemorySelectionItem({ ...(cell.base as MemorySelectionItem) }) : null,
    implicit: [...(cell.implicit as MemorySelectionItem[])].map(r =>
      normalizeMemorySelectionItem({ ...r })
    ),
    random: [...(cell.random as MemorySelectionItem[])].map(r =>
      normalizeMemorySelectionItem({ ...r })
    )
  }
}

/** 从 buildStore 拉取追忆选择（进入页面 / 路由返回时与持久化快照一致） */
function applyMemoriesFromStore() {
  const ps = buildStore.snapshot.memories?.perSource ?? {}
  const next = createEmptyPerSourceRecord()
  for (const id of MEMORY_ITEM_SOURCE_IDS) {
    const cell = ps[id]
    next[id] = cell ? cloneCell(cell as MemoryPerSourceSelections) : { base: null, implicit: [], random: [] }
  }
  for (const [id, cell] of Object.entries(ps)) {
    if ((MEMORY_ITEM_SOURCE_IDS as readonly string[]).includes(id)) continue
    if (cell && typeof cell === 'object') {
      next[id] = cloneCell(cell as MemoryPerSourceSelections)
    }
  }
  perSource.value = next
}

applyMemoriesFromStore()

function memoryShortLabel(fullName: string): string {
  const n = fullName.replace(/的追忆$/, '')
  return n.length ? n : fullName
}

function quotaFor(sourceId: string): { base: number; implicit: number; random: number } {
  const c = perSource.value[sourceId] ?? { base: null, implicit: [], random: [] }
  return {
    base: c.base ? 1 : 0,
    implicit: c.implicit?.length ?? 0,
    random: c.random?.length ?? 0
  }
}

const query = ref('')
const sourceFilter = ref<'all' | string>('all')
const categoryFilter = ref<'all' | string>('all')
const tierFilter = ref<'all' | string>('all')

const categoryTabs = [
  { id: 'all', label: '全部类型' },
  { id: '基础属性', label: '基础属性' },
  { id: '固有词缀', label: '固有词缀' },
  { id: '随机词缀', label: '随机词缀' }
]

const tierTabsAll = [
  { id: 'all', label: '全部Tier' },
  { id: 'T0', label: 'T0' },
  { id: 'T1', label: 'T1' },
  { id: 'T2', label: 'T2' },
  { id: 'T3', label: 'T3' }
]

/** 固有词缀无 T0（仅 T1–T3）；随机词缀含 T0–T3 */
const tierTabsForFilter = computed(() => {
  if (categoryFilter.value === '固有词缀') {
    return tierTabsAll.filter(t => t.id !== 'T0')
  }
  return tierTabsAll
})

/** 仅「基础属性」分类下列表不展示 Tier 列（基础词缀恒为 T1，无区分意义） */
const showTierColumn = computed(() => categoryFilter.value !== '基础属性')

watch(categoryFilter, val => {
  if (val === '固有词缀' && tierFilter.value === 'T0') {
    tierFilter.value = 'all'
  }
  if (val === '基础属性') {
    tierFilter.value = 'all'
  }
})

function tierCellText(row: AffixRow): string {
  if (row.category === '基础属性') return '—'
  return row.tierLabel || '—'
}

function affixKey(row: AffixRow | MemorySelectionItem): string {
  const id = String(row.modifierId ?? '').trim()
  if (id) {
    return `${id}|${row.sourceId}|${row.category}|${String(row.tierLabel ?? '')}`
  }
  const raw =
    'effectTextRaw' in row && row.effectTextRaw
      ? String(row.effectTextRaw)
      : String((row as AffixRow).effectText ?? '')
  return `${row.sourceId}|${raw}|${row.category}|${String(row.tierLabel ?? '')}`
}

function toMemorySelection(row: AffixRow): MemorySelectionItem {
  return normalizeMemorySelectionItem({
    modifierId: row.modifierId,
    effectText: row.effectText,
    sourceId: row.sourceId,
    sourceName: row.sourceName,
    sourcePath: row.sourcePath,
    category: row.category,
    tier: row.tier ?? null,
    tierLabel: row.tierLabel,
    level: row.level ?? null,
    weight: row.weight ?? null,
    memoryRarity: row.memoryRarity
  })
}

function onMemoryRangeChange(
  sourceId: string,
  kind: 'base' | 'implicit' | 'random',
  slotIndex: number,
  rangeIndex: number,
  valueStr: string
) {
  const cell = perSource.value[sourceId]
  if (!cell) return
  const v = Number(valueStr)
  if (!Number.isFinite(v)) return
  if (kind === 'base') {
    if (!cell.base) return
    const next = patchMemoryItemRangePick(cell.base as MemorySelectionItem, rangeIndex, v)
    perSource.value = { ...perSource.value, [sourceId]: { ...cell, base: next } }
    return
  }
  if (kind === 'implicit') {
    const arr = [...cell.implicit] as MemorySelectionItem[]
    const cur = arr[slotIndex]
    if (!cur) return
    arr[slotIndex] = patchMemoryItemRangePick(cur, rangeIndex, v)
    perSource.value = { ...perSource.value, [sourceId]: { ...cell, implicit: arr } }
    return
  }
  const arr = [...cell.random] as MemorySelectionItem[]
  const cur = arr[slotIndex]
  if (!cur) return
  arr[slotIndex] = patchMemoryItemRangePick(cur, rangeIndex, v)
  perSource.value = { ...perSource.value, [sourceId]: { ...cell, random: arr } }
}

function isRowSelected(row: AffixRow): boolean {
  const k = affixKey(row)
  const sid = row.sourceId
  const cell = perSource.value[sid]
  if (!cell) return false
  if (row.category === '基础属性') {
    return cell.base != null && affixKey(cell.base as MemorySelectionItem) === k
  }
  if (row.category === '固有词缀') {
    return cell.implicit.some(r => affixKey(r as MemorySelectionItem) === k)
  }
  if (row.category === '随机词缀') {
    return cell.random.some(r => affixKey(r as MemorySelectionItem) === k)
  }
  return false
}

function toggleSelect(row: AffixRow) {
  const k = affixKey(row)
  const sid = row.sourceId
  const prev = perSource.value[sid] ?? { base: null, implicit: [], random: [] }
  const cell: MemoryPerSourceSelections = {
    base: prev.base,
    implicit: [...prev.implicit],
    random: [...prev.random]
  }

  if (row.category === '基础属性') {
    const cur = cell.base as MemorySelectionItem | null
    if (cur && affixKey(cur) === k) {
      cell.base = null
    } else {
      cell.base = toMemorySelection(row)
    }
    perSource.value = { ...perSource.value, [sid]: cell }
    return
  }
  if (row.category === '固有词缀') {
    const arr = cell.implicit as MemorySelectionItem[]
    const i = arr.findIndex(r => affixKey(r) === k)
    if (i >= 0) {
      cell.implicit = arr.filter((_, j) => j !== i)
    } else if (arr.length < 2) {
      cell.implicit = [...arr, toMemorySelection(row)]
    } else {
      cell.implicit = [arr[1]!, toMemorySelection(row)]
    }
    perSource.value = { ...perSource.value, [sid]: cell }
    return
  }
  if (row.category === '随机词缀') {
    const arr = cell.random as MemorySelectionItem[]
    const i = arr.findIndex(r => affixKey(r) === k)
    if (i >= 0) {
      cell.random = arr.filter((_, j) => j !== i)
    } else if (arr.length < 2) {
      cell.random = [...arr, toMemorySelection(row)]
    } else {
      cell.random = [arr[1]!, toMemorySelection(row)]
    }
    perSource.value = { ...perSource.value, [sid]: cell }
  }
}

watch(
  perSource,
  () => {
    buildStore.setMemorySelectionsPerSource(perSource.value)
  },
  { deep: true }
)

onMounted(applyMemoriesFromStore)
onActivated(applyMemoriesFromStore)

function tlidbUrl(path: string): string {
  if (path.startsWith('http')) return path
  return `https://tlidb.com${path.startsWith('/') ? '' : '/'}${path}`
}

/** 按三种追忆物品（本源 / 守己 / 奋进）分别统计已选的基础 / 固有 / 随机条数与效果 */
const pickedByMemory = computed(() => {
  return items.map(it => {
    const sid = it.id
    const cell = perSource.value[sid] ?? { base: null, implicit: [], random: [] }
    const base = (cell.base as MemorySelectionItem | null) ?? null
    const implicit = (cell.implicit as MemorySelectionItem[]) ?? []
    const random = (cell.random as MemorySelectionItem[]) ?? []
    const countBase = base ? 1 : 0
    const total = countBase + implicit.length + random.length
    return {
      id: sid,
      name: it.name,
      base,
      implicit,
      random,
      total,
      countBase
    }
  })
})

const filteredAffixes = computed((): AffixRow[] => {
  const q = query.value.trim().toLowerCase()
  let list = affixes
  if (sourceFilter.value !== 'all') {
    list = list.filter(a => a.sourceId === sourceFilter.value)
  }
  if (categoryFilter.value !== 'all') {
    list = list.filter(a => a.category === categoryFilter.value)
  }
  if (categoryFilter.value === '固有词缀') {
    list = list.filter(a => (a.tierLabel ?? '') !== 'T0')
  }
  if (tierFilter.value !== 'all' && categoryFilter.value !== '基础属性') {
    list = list.filter(a => (a.tierLabel ?? '') === tierFilter.value)
  }
  if (q) {
    list = list.filter(a => {
      if (a.effectText.toLowerCase().includes(q)) return true
      if (a.sourceName.toLowerCase().includes(q)) return true
      if (a.category.toLowerCase().includes(q)) return true
      if ((a.tierLabel ?? '').toLowerCase().includes(q)) return true
      return false
    })
  }
  return list
})
</script>

<style scoped>
.hm-page {
  box-sizing: border-box;
  height: calc(100dvh - var(--app-header-height, 4.75rem));
  min-height: 0;
  display: flex;
  width: 100%;
  max-width: none;
  margin: 0;
  padding: 18px;
  gap: 20px;
  color: #fff;
  overflow: hidden;
}

.hm-sidebar {
  width: min(340px, 36vw);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow-x: hidden;
  overflow-y: auto;
}

.hm-sidebar-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.hm-sidebar-head h2 {
  margin: 0;
  font-size: 20px;
}

.hm-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.hm-tip {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.55);
}

.hm-tip code {
  font-size: 11px;
  color: rgba(180, 220, 255, 0.9);
}

.hm-tip a {
  color: rgba(126, 200, 255, 0.95);
}

.hm-items {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 10px;
}

.hm-item-card {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.22);
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.hm-item-memory {
  width: calc((100% - 16px) / 3);
  min-width: 0;
  padding: 8px 6px;
  flex-direction: column;
  align-items: center;
  text-align: center;
  gap: 6px;
}

.hm-item-memory .hm-item-text {
  align-items: center;
}

.hm-item-memory .hm-item-name {
  font-size: 12px;
}

.hm-item-memory .hm-item-link {
  align-self: center;
}

.hm-item-memory .hm-item-icon-wrap {
  width: 40px;
  height: 40px;
}

.hm-item-card:hover {
  border-color: rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.08);
}

.hm-item-card.active {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.15);
}

.hm-item-all {
  width: 100%;
  padding-left: 12px;
}

.hm-item-icon-wrap {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
}

.hm-item-icon {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.hm-item-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.hm-item-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
}

.hm-item-sub {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
}

.hm-item-link {
  font-size: 11px;
  color: rgba(126, 200, 255, 0.95);
  text-decoration: none;
  align-self: flex-start;
}

.hm-item-link:hover {
  text-decoration: underline;
}

.hm-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.hm-filter-tab {
  padding: 5px 11px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(0, 0, 0, 0.25);
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.hm-filter-tab:hover {
  border-color: rgba(233, 69, 96, 0.45);
  color: #fff;
}

.hm-filter-tab.active {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.15);
  color: #fff;
}

.hm-search {
  margin-bottom: 12px;
}

.hm-picked {
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  flex-shrink: 0;
}

.hm-picked-title {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
  margin-bottom: 6px;
}

.hm-picked-hint {
  margin: 0 0 10px;
  font-size: 11px;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.42);
}

.hm-picked-section {
  margin-bottom: 12px;
}

.hm-picked-section:last-child {
  margin-bottom: 0;
}

.hm-picked-label {
  font-size: 11px;
  font-weight: 600;
  color: rgba(200, 215, 255, 0.75);
  margin-bottom: 6px;
}

.hm-picked-cap {
  font-weight: 600;
  color: rgba(240, 210, 150, 0.95);
}

.hm-picked-empty {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.35);
}

.hm-picked-item {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 6px 8px;
  margin-bottom: 6px;
  border-radius: 8px;
  background: rgba(233, 69, 96, 0.1);
  border: 1px solid rgba(233, 69, 96, 0.28);
  font-size: 11px;
  line-height: 1.35;
}

.hm-picked-meta {
  flex-shrink: 0;
  min-width: 1.5rem;
  font-weight: 700;
  color: rgba(240, 210, 150, 0.95);
}

.hm-picked-text {
  flex: 1;
  min-width: 0;
  color: rgba(255, 255, 255, 0.88);
}

.hm-picked-remove {
  flex-shrink: 0;
  width: 22px;
  height: 22px;
  padding: 0;
  border: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.75);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
}

.hm-picked-remove:hover {
  background: rgba(233, 69, 96, 0.35);
  color: #fff;
}

.hm-picked-global {
  margin: 0 0 12px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(230, 238, 255, 0.88);
  line-height: 1.45;
}

.hm-picked-mem-quota {
  margin-right: 4px;
}

.hm-picked-dot {
  margin: 0 5px;
  color: rgba(255, 255, 255, 0.35);
}

.hm-picked-by-mem {
  margin-bottom: 14px;
}

.hm-picked-subtitle {
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.02em;
  color: rgba(200, 215, 255, 0.75);
  margin-bottom: 8px;
}

.hm-picked-subtitle-detail {
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.hm-mem-block {
  margin-bottom: 10px;
  padding: 8px 10px;
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hm-mem-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.hm-mem-name {
  font-size: 13px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.92);
}

.hm-mem-total {
  font-size: 12px;
  font-weight: 600;
  color: rgba(240, 210, 150, 0.95);
}

.hm-mem-list {
  margin: 0;
  padding: 0;
  list-style: none;
}

.hm-mem-line {
  display: grid;
  grid-template-columns: 2.25rem 2.5rem 1fr;
  gap: 6px 8px;
  align-items: start;
  font-size: 12px;
  line-height: 1.4;
  margin-bottom: 6px;
}

.hm-mem-line:last-child {
  margin-bottom: 0;
}

.hm-mem-k {
  color: rgba(180, 200, 255, 0.65);
  font-weight: 600;
}

.hm-mem-n {
  color: rgba(255, 255, 255, 0.45);
  font-weight: 600;
  text-align: right;
}

.hm-mem-v {
  color: rgba(255, 255, 255, 0.88);
  word-break: break-word;
}

.hm-mem-chip {
  display: block;
  margin-top: 4px;
  padding-left: 0.25rem;
  border-left: 2px solid rgba(233, 69, 96, 0.45);
}

.hm-mem-chip:first-child {
  margin-top: 0;
}

.hm-mem-inline-entry {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 8px;
  margin-bottom: 6px;
  font-size: 11px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.88);
  word-break: break-word;
}

.hm-mem-inline-entry--list {
  padding-bottom: 6px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.hm-mem-inline-entry--list:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.hm-inline-tier {
  flex-shrink: 0;
  padding: 1px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  color: rgba(240, 210, 150, 0.95);
  background: rgba(233, 69, 96, 0.15);
  border: 1px solid rgba(233, 69, 96, 0.35);
}

.hm-inline-fx {
  display: inline-flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 0 2px;
  vertical-align: baseline;
  min-width: 0;
}

.hm-inline-txt {
  white-space: pre-wrap;
  vertical-align: baseline;
}

.hm-inline-sel {
  display: inline-block;
  vertical-align: baseline;
  margin: 0 1px;
  min-width: 2.75rem;
  max-width: 4.5rem;
  padding: 0 4px;
  height: 1.35rem;
  line-height: 1.2;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(20, 22, 32, 0.95);
  color: rgba(255, 230, 200, 0.98);
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.hm-inline-sel:focus {
  outline: 1px solid rgba(233, 69, 96, 0.6);
  border-color: rgba(233, 69, 96, 0.5);
}

.hm-search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 11px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  font-size: 13px;
}

.hm-main {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.hm-table-wrap {
  flex: 1;
  min-height: 0;
  overflow: auto;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
}

.hm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.hm-table thead th {
  position: sticky;
  top: 0;
  z-index: 1;
  background: rgba(22, 22, 32, 0.96);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding: 10px 12px;
  text-align: left;
  font-weight: 600;
  color: rgba(235, 244, 255, 0.9);
}

.hm-table tbody td {
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  padding: 8px 12px;
  vertical-align: top;
}

.hm-data-row {
  cursor: pointer;
}

.hm-data-row:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.65);
  outline-offset: -2px;
}

.hm-table tbody tr.hm-row-selected td {
  background: rgba(233, 69, 96, 0.12);
}

.hm-table tbody tr.hm-row-selected:hover td {
  background: rgba(233, 69, 96, 0.18);
}

.hm-table tbody tr.hm-data-row:hover td {
  background: rgba(233, 69, 96, 0.06);
}

.hm-table tbody tr.hm-data-row.hm-row-selected:hover td {
  background: rgba(233, 69, 96, 0.18);
}

.hm-col-effect {
  width: 48%;
}

.hm-col-source {
  width: 24%;
}

.hm-col-cat {
  width: 20%;
  color: rgba(200, 220, 255, 0.72);
}

.hm-col-tier {
  width: 8%;
  color: rgba(240, 210, 150, 0.9);
  font-weight: 600;
}

.hm-col-source a {
  color: rgba(126, 200, 255, 0.95);
  text-decoration: none;
}

.hm-col-source a:hover {
  text-decoration: underline;
}

.hm-empty {
  margin: 24px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}
</style>
