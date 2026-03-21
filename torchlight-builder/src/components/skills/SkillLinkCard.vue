<template>
  <div class="skill-link-card-root">
  <Teleport to="body">
    <div
      v-if="detailPopover.skill"
      class="skill-detail-popover"
      :style="{ top: detailPopover.top + 'px', left: detailPopover.left + 'px' }"
      role="tooltip"
      @mouseenter="cancelHidePopover"
      @mouseleave="scheduleHidePopover"
    >
      <div class="skill-detail-popover-inner">
        <div
          v-if="detailPopover.skill.iconUrl"
          class="skill-detail-popover-icon-wrap"
        >
          <img
            :src="detailPopover.skill.iconUrl"
            :alt="detailPopover.skill.name"
            class="skill-detail-popover-icon"
            loading="lazy"
          />
        </div>
        <div class="skill-detail-popover-body">
          <div class="skill-detail-popover-name">{{ detailPopover.skill.name }}</div>
          <div
            v-if="detailPopover.skill.tags?.length"
            class="skill-detail-popover-tags"
          >
            <span
              v-for="t in detailPopover.skill.tags"
              :key="t"
              class="skill-detail-tag"
            >
              {{ t }}
            </span>
          </div>
          <div
            v-if="
              detailPopover.skill.statRows?.length ||
              spellLevel20BaseDamageRange(detailPopover.skill) ||
              detailPopover.skill.supportDamageBonusByTier?.length === 3
            "
            class="skill-detail-popover-stats"
          >
            <template v-if="detailPopover.skill.statRows?.length">
              <div
                v-for="(row, ri) in detailPopover.skill.statRows"
                :key="`${row.label}-${ri}`"
                class="skill-detail-stat-row"
              >
                <span class="skill-detail-stat-label">{{ row.label }}</span>
                <span class="skill-detail-stat-value">{{ row.value }}</span>
              </div>
            </template>
            <template v-if="detailPopover.skill.supportDamageBonusByTier?.length === 3">
              <div
                v-for="(tv, tvi) in detailPopover.skill.supportDamageBonusByTier"
                :key="`tier-${tvi}`"
                class="skill-detail-stat-row"
              >
                <span class="skill-detail-stat-label">增伤 T{{ tvi }}</span>
                <span class="skill-detail-stat-value">{{
                  String(tv).includes('%') ? tv : `${tv}%`
                }}</span>
              </div>
            </template>
            <div
              v-if="spellLevel20BaseDamageRange(detailPopover.skill)"
              class="skill-detail-stat-row"
            >
              <span class="skill-detail-stat-label">20级基础点伤</span>
              <span class="skill-detail-stat-value skill-detail-stat-value--spell-flat">{{
                spellLevel20BaseDamageRange(detailPopover.skill)
              }}</span>
            </div>
          </div>
          <a
            class="skill-detail-wiki"
            :href="wikiSkillPageUrl(detailPopover.skill.id)"
            target="_blank"
            rel="noopener noreferrer"
            @click.stop
          >
            在 tlidb 查看详情 ↗
          </a>
        </div>
      </div>
    </div>
  </Teleport>

  <div class="skill-card">
    <div class="skill-card-head">
      <div class="skill-card-title-wrap">
        <div class="skill-card-title" :title="headerTitle">{{ headerTitle }}</div>
        <div class="skill-card-role" :class="`role-${role}`">{{ roleLabel }}</div>
      </div>
      <div class="skill-card-count">辅助连接 {{ supportCount }}/5</div>
    </div>

    <div class="skill-card-split">
      <div class="skill-split-left">
        <div class="link-diagram link-diagram--split">
          <button
            v-if="hasAnySkillSelection"
            type="button"
            class="link-diagram-clear-all"
            title="清空主技能与全部辅助"
            aria-label="清空全部已选技能"
            @click="clearAllSkills"
          >
            清空
          </button>
          <svg class="link-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
            <line
              v-for="(p, idx) in supportPoints"
              :key="`line-${idx}`"
              x1="50"
              y1="50"
              :x2="p.x"
              :y2="p.y"
              stroke="rgba(255,255,255,0.24)"
              stroke-width="1.2"
            />
          </svg>

          <div
            class="node node-main"
            :class="{ active: editingSlot === 'main', filled: !!mainSkillName }"
            @mouseenter="onMainNodeDetailEnter($event)"
            @mouseleave="scheduleHidePopover"
          >
            <button
              type="button"
              class="node-body"
              :aria-label="mainSkillName ? `主技能：${mainSkillName}` : '选择主技能'"
              @click="selectMainEditingSlot"
            >
              <span class="node-icon-wrap" :class="{ 'node-icon-wrap--empty': !mainSkillIconUrl }">
                <img
                  v-if="mainSkillIconUrl"
                  :src="mainSkillIconUrl"
                  :alt="mainSkillName || '主技能'"
                  class="node-icon-img"
                  loading="lazy"
                />
              </span>
              <span class="node-name">{{ mainSkillName || '点击选择技能' }}</span>
            </button>
            <button
              v-if="hasMainSkillSelection"
              type="button"
              class="node-clear"
              title="取消选择"
              aria-label="取消主技能"
              @click.stop="clearMainSkill"
            >
              ×
            </button>
          </div>

          <div
            v-for="(slot, idx) in supportSlotsMeta"
            :key="`support-${idx}`"
            class="node node-support"
            :class="{
              active: editingSlot === idx,
              filled: !!slot.name,
              'node-support--locked': !hasMainSkillSelection
            }"
            :style="supportNodeStyleByIndex(idx)"
            @mouseenter="onSupportNodeDetailEnter(idx, $event)"
            @mouseleave="scheduleHidePopover"
          >
            <button
              type="button"
              class="node-body"
              :disabled="!hasMainSkillSelection"
              :aria-label="
                hasMainSkillSelection
                  ? `辅助技能 ${idx + 1}${slot.name ? `：${slot.name}` : ''}`
                  : `辅助 ${idx + 1}，请先选择主技能`
              "
              @click="onSupportSlotClick(idx)"
            >
              <span class="node-slot-badge" aria-hidden="true">{{ idx + 1 }}</span>
              <span
                class="node-icon-wrap node-icon-wrap--support"
                :class="{ 'node-icon-wrap--empty': !slot.iconUrl }"
              >
                <img
                  v-if="slot.iconUrl"
                  :src="slot.iconUrl"
                  :alt="slot.name || `辅助 ${idx + 1}`"
                  class="node-icon-img"
                  loading="lazy"
                />
              </span>
              <span class="node-name node-name--support">{{ slot.name || '未连接' }}</span>
            </button>
            <button
              v-if="hasSupportSelection(idx)"
              type="button"
              class="node-clear node-clear--support"
              title="取消选择"
              :aria-label="`取消辅助技能 ${idx + 1}`"
              @click.stop="clearSupportSkill(idx)"
            >
              ×
            </button>
          </div>
        </div>
      </div>

      <div class="skill-split-right">
        <div class="selection-data-panel">
          <div class="selection-data-head">已选技能与数值</div>
          <div v-if="!hasAnySkillSelection" class="selection-data-empty">
            在左侧图中点击节点，在此查看等级与倍率
          </div>
          <div v-else class="selection-data-list">
            <div v-if="hasMainSkillSelection" class="selection-block selection-block--main">
              <div class="selection-block-title">主技能</div>
              <div class="selection-block-name">{{ mainSkillName }}</div>
              <label class="selection-level-row">
                <span class="selection-level-label">等级</span>
                <select
                  class="selection-level-select"
                  :value="effectiveLink.mainSkillLevel"
                  :disabled="role === 'passive'"
                  @change="onMainLevelChange"
                >
                  <option v-for="lv in mainLevelRange" :key="`ml-${lv}`" :value="lv">
                    {{ lv }}
                  </option>
                </select>
              </label>
              <div class="selection-stat-lines">
                <div class="selection-stat-line">
                  <span class="selection-stat-k">伤害倍率</span>
                  <span class="selection-stat-v">{{ mainMultiplierDisplay }}</span>
                </div>
                <div
                  v-if="mainBaseDamageDisplay !== null"
                  class="selection-stat-line"
                >
                  <span class="selection-stat-k">基础点伤</span>
                  <span class="selection-stat-v">{{ mainBaseDamageDisplay }}</span>
                </div>
              </div>
            </div>

            <template v-for="sIdx in 5" :key="`sd-${sIdx}`">
              <div
                v-if="hasSupportSelection(sIdx - 1)"
                class="selection-block selection-block--support"
              >
                <div class="selection-block-title">辅助 {{ sIdx }}</div>
                <div class="selection-block-name">
                  {{ supportSlotsMeta[sIdx - 1]?.name }}
                </div>
                <label class="selection-level-row selection-level-row--support-lv">
                  <span class="selection-level-label">{{ supportLevelLabelForSlot(sIdx - 1) }}</span>
                  <select
                    class="selection-level-select"
                    :value="effectiveLink.supportSkillLevels[sIdx - 1]"
                    @change="e => onSupportLevelChange(sIdx - 1, e)"
                  >
                    <option
                      v-for="lv in supportLevelRangeForSlot(sIdx - 1)"
                      :key="`sl-${sIdx}-${lv}`"
                      :value="lv"
                    >
                      {{ supportLevelOptionLabel(sIdx - 1, lv) }}
                    </option>
                  </select>
                  <input
                    v-if="isExclusiveTierSupportSlot(sIdx - 1)"
                    class="selection-exclusive-value-input"
                    type="text"
                    inputmode="decimal"
                    autocomplete="off"
                    spellcheck="false"
                    placeholder="自定义%"
                    :value="effectiveLink.supportExclusiveCustomBonuses[sIdx - 1]"
                    @input="onExclusiveCustomBonusInput(sIdx - 1, $event)"
                  />
                </label>
                <div class="selection-stat-lines">
                  <div class="selection-stat-line">
                    <span class="selection-stat-k">辅助增伤</span>
                    <span class="selection-stat-v">{{ supportBonusDisplay(sIdx - 1) }}</span>
                  </div>
                </div>
              </div>
            </template>
          </div>
        </div>
      </div>
    </div>

    <div class="picker-panel picker-panel--below">
      <div class="picker-head">
        <span class="picker-title">{{ pickerTitle }}</span>
      </div>
      <div class="picker-options">
        <div class="picker-search-row">
          <input
            v-model="pickerSearchQuery"
            type="search"
            class="picker-search-input"
            placeholder="按技能名称搜索…"
            enterkeyhint="search"
            autocomplete="off"
            spellcheck="false"
          />
          <button
            type="button"
            class="picker-reset"
            :disabled="!pickerSearchQuery.trim() && selectedFilterTags.length === 0"
            title="清空搜索与标签筛选"
            @click="resetPickerFilters"
          >
            重置
          </button>
        </div>
        <div class="picker-tags">
          <button
            v-for="tag in availableTags"
            :key="`tag-${tag}`"
            type="button"
            class="tag-chip"
            :class="{ active: isFilterTagActive(tag) }"
            @click="onFilterTagClick(tag, $event)"
          >
            {{ tag }}
          </button>
        </div>
        <div class="picker-divider"></div>
        <div class="opt-list">
          <button
            v-for="opt in filteredOptions"
            :key="opt.id"
            type="button"
            class="opt-chip"
            @click="applyOption(opt.id)"
            @mouseenter="onPickerSkillEnter(opt, $event)"
            @mouseleave="scheduleHidePopover"
            @focus="onPickerSkillEnter(opt, $event)"
            @blur="scheduleHidePopover"
          >
            <img
              v-if="opt.iconUrl"
              :src="opt.iconUrl"
              :alt="opt.name"
              class="opt-icon"
              loading="lazy"
            />
            <span class="opt-name">{{ opt.name }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

type SkillStatRow = { label: string; value: string }

type SkillOption = {
  id: string
  name: string
  iconUrl?: string
  tags?: string[]
  statRows?: SkillStatRow[]
  damageMultiplierByLevel?: string[]
  skillBaseDamageByLevel?: string[]
  supportDamageBonusByLevel?: string[]
  /** 崇高/华贵等：T0–T2 三档增伤展示（与 wiki Tier 0/1/2 对应） */
  supportDamageBonusByTier?: string[]
}

type SkillLinkItem = {
  mainSkillId: string
  supportSkillIds: string[]
  mainSkillLevel?: number
  supportSkillLevels?: number[]
  /** 与辅槽一一对应；崇高/华贵 T 级下用户可填自定义增伤数值（覆盖下方「辅助增伤」展示） */
  supportExclusiveCustomBonuses?: string[]
}

/** linkWithDefaults 输出，等级与辅槽数组始终完整 */
type NormalizedSkillLink = {
  mainSkillId: string
  supportSkillIds: string[]
  mainSkillLevel: number
  supportSkillLevels: number[]
  supportExclusiveCustomBonuses: string[]
}

const MAIN_LEVEL_MAX = 20
const SUPPORT_LEVEL_MAX = 40
/**
 * 封印转化 / 精密 封印转化：wiki 上仅标「辅助」，但与「光环」类主技能可连携，标签交集规则会误排除，需显式放行。
 * id 与 supportSkillTags.json 一致（精密为 URL 编码形式）。
 */
const AURA_SUPPORT_LINK_IDS: readonly string[] = ['Seal_Conversion', 'Precise%3A_Seal_Conversion']

/** 新槽 / 新选技能时的默认等级（主技能上限 20） */
const DEFAULT_MAIN_SKILL_LEVEL = 20
const DEFAULT_SUPPORT_SKILL_LEVEL = 20
/** 专属辅助三档：默认选中 T2（wiki Tier 2） */
const DEFAULT_EXCLUSIVE_TIER_LEVEL = 3

/** 与 Skills.vue 中 mapSupportJsonToOptions 写入的 tags 一致 */
const EXCLUSIVE_NOBLE_SUPPORT_TAG = '崇高'
const EXCLUSIVE_MAGNIFICENT_SUPPORT_TAG = '华贵'

function isExclusiveNobleSupport(opt: SkillOption): boolean {
  return (opt.tags ?? []).some(t => (t ?? '').trim() === EXCLUSIVE_NOBLE_SUPPORT_TAG)
}

function isExclusiveMagnificentSupport(opt: SkillOption): boolean {
  return (opt.tags ?? []).some(t => (t ?? '').trim() === EXCLUSIVE_MAGNIFICENT_SUPPORT_TAG)
}

function isExclusiveSupportOpt(opt: SkillOption): boolean {
  return isExclusiveNobleSupport(opt) || isExclusiveMagnificentSupport(opt)
}

/** wiki 专属辅助 slug 含 (Noble)/(Magnificent)，与是否已写入 supportDamageBonusByTier 无关 */
function isWikiExclusiveSupportSkillId(skillId: string): boolean {
  const id = skillId.trim()
  if (!id) return false
  const u = id.toLowerCase()
  if (u.includes("%28noble%29") || u.includes("%28magnificent%29")) return true
  try {
    const dec = decodeURIComponent(id).toLowerCase()
    return dec.includes("(noble)") || dec.includes("(magnificent)")
  } catch {
    return false
  }
}

/** tlidb 专属辅助 id：{主动技能 id}%3A..._(Noble|Magnificent) */
function exclusiveSupportLinkedMainId(supportId: string): string | null {
  const id = supportId.trim()
  const sep = '%3A'
  const i = id.indexOf(sep)
  if (i <= 0) return null
  return id.slice(0, i).trim()
}

/** 华贵专属仅第 3 辅槽；崇高专属仅第 5 辅槽（均为 1-based 槽位 → 0-based 索引 2、4） */
const MAGNIFICENT_EXCLUSIVE_SUPPORT_SLOT_INDEX = 2
const NOBLE_EXCLUSIVE_SUPPORT_SLOT_INDEX = 4

function exclusiveSkillAllowedInSupportSlot(opt: SkillOption, slotIndex: number): boolean {
  if (isExclusiveNobleSupport(opt)) return slotIndex === NOBLE_EXCLUSIVE_SUPPORT_SLOT_INDEX
  if (isExclusiveMagnificentSupport(opt)) return slotIndex === MAGNIFICENT_EXCLUSIVE_SUPPORT_SLOT_INDEX
  return true
}

type SkillRole = 'core' | 'active' | 'passive'

interface Props {
  title: string
  role: SkillRole
  modelValue: SkillLinkItem
  mainOptions: SkillOption[]
  supportOptions: SkillOption[]
  /** 选辅助槽时的标签白名单（与 wiki 辅助技能 Tag 一致） */
  tagWhitelist?: string[]
  /** 选主技能槽时的标签白名单（主动技能用 activeSkillTags；被动可单独传） */
  mainTagWhitelist?: string[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SkillLinkItem): void
}>()

function clampMainLevel(n: unknown): number {
  const x = Math.round(Number(n))
  if (Number.isNaN(x) || x < 1) return 1
  return Math.min(MAIN_LEVEL_MAX, x)
}

function supportLevelMaxForSkillId(skillId: string): number {
  const id = skillId.trim()
  if (!id) return SUPPORT_LEVEL_MAX
  const opt = props.supportOptions.find(o => (o.id ?? '').trim() === id)
  if (opt?.supportDamageBonusByTier?.length === 3) return 3
  return SUPPORT_LEVEL_MAX
}

function clampSupportLevelForSkillId(n: unknown, skillId: string): number {
  const x = Math.round(Number(n))
  const max = supportLevelMaxForSkillId(skillId)
  if (Number.isNaN(x) || x < 1) return 1
  return Math.min(max, x)
}

function linkWithDefaults(v: SkillLinkItem): NormalizedSkillLink {
  const ids = [...(v.supportSkillIds ?? [])]
  while (ids.length < 5) ids.push('')
  const sl = [...(v.supportSkillLevels ?? [])]
  while (sl.length < 5) sl.push(DEFAULT_SUPPORT_SKILL_LEVEL)
  const customs = [...(v.supportExclusiveCustomBonuses ?? [])]
  while (customs.length < 5) customs.push('')
  let ml = clampMainLevel(v.mainSkillLevel ?? DEFAULT_MAIN_SKILL_LEVEL)
  if (props.role === 'passive') ml = 1
  const normIds = ids.slice(0, 5).map(s => String(s ?? ''))
  return {
    mainSkillId: String(v.mainSkillId ?? ''),
    supportSkillIds: normIds,
    mainSkillLevel: ml,
    supportSkillLevels: sl.slice(0, 5).map((x, i) =>
      clampSupportLevelForSkillId(x ?? DEFAULT_SUPPORT_SKILL_LEVEL, normIds[i] ?? '')
    ),
    supportExclusiveCustomBonuses: customs.slice(0, 5).map(s => String(s ?? ''))
  }
}

function emitLink(partial: Partial<SkillLinkItem>) {
  emit('update:modelValue', linkWithDefaults({ ...props.modelValue, ...partial }))
}

const effectiveLink = computed(() => linkWithDefaults(props.modelValue))

const mainLevelRange = computed(() =>
  Array.from({ length: MAIN_LEVEL_MAX }, (_, i) => i + 1)
)

function supportLevelRangeForSlot(slotIdx: number): number[] {
  const max = supportLevelMaxForSkillId((props.modelValue.supportSkillIds[slotIdx] ?? '').trim())
  return Array.from({ length: max }, (_, i) => i + 1)
}

function supportLevelLabelForSlot(slotIdx: number): string {
  return supportLevelMaxForSkillId((props.modelValue.supportSkillIds[slotIdx] ?? '').trim()) === 3
    ? 'T 级'
    : '等级'
}

function supportLevelOptionLabel(slotIdx: number, lv: number): string {
  if (supportLevelMaxForSkillId((props.modelValue.supportSkillIds[slotIdx] ?? '').trim()) === 3) {
    return `T${lv - 1}`
  }
  return String(lv)
}

const mainMultiplierDisplay = computed(() => {
  const opt = mainSkillOption.value
  const lv = effectiveLink.value.mainSkillLevel
  const arr = opt?.damageMultiplierByLevel
  if (!arr?.length || lv < 1 || lv > arr.length) return '—'
  const s = (arr[lv - 1] ?? '').trim()
  return s || '—'
})

const mainBaseDamageDisplay = computed(() => {
  const opt = mainSkillOption.value
  const lv = effectiveLink.value.mainSkillLevel
  const arr = opt?.skillBaseDamageByLevel
  if (!arr?.length || lv < 1 || lv > arr.length) return null
  const s = (arr[lv - 1] ?? '').trim()
  return s.length > 0 ? s : null
})

function supportBonusDisplay(slotIdx: number): string {
  const id = (props.modelValue.supportSkillIds[slotIdx] ?? '').trim()
  if (!id) return '—'
  const customRaw = (effectiveLink.value.supportExclusiveCustomBonuses[slotIdx] ?? '').trim()
  if (customRaw.length > 0) {
    if (/^\d+(\.\d+)?$/.test(customRaw)) return `${customRaw}%`
    return customRaw
  }
  const opt = props.supportOptions.find(o => o.id === id)
  const lvRaw = effectiveLink.value.supportSkillLevels[slotIdx] ?? DEFAULT_SUPPORT_SKILL_LEVEL
  const tiers = opt?.supportDamageBonusByTier
  const wikiExclusive = isWikiExclusiveSupportSkillId(id)
  if (wikiExclusive || tiers?.length === 3) {
    if (!tiers?.length) return '—'
    const lv = Math.min(Math.max(Math.round(lvRaw), 1), 3)
    const s = (tiers[lv - 1] ?? '').trim()
    if (!s) return '—'
    return s.includes('%') ? s : `${s}%`
  }
  const arr = opt?.supportDamageBonusByLevel
  if (!arr?.length || lvRaw < 1 || lvRaw > arr.length) return '—'
  const s = (arr[lvRaw - 1] ?? '').trim()
  return s ? `${s}%` : '—'
}

function onMainLevelChange(e: Event) {
  const el = e.target as HTMLSelectElement
  emitLink({ mainSkillLevel: clampMainLevel(el.value) })
}

function onSupportLevelChange(slotIdx: number, e: Event) {
  const el = e.target as HTMLSelectElement
  const sid = (props.modelValue.supportSkillIds[slotIdx] ?? '').trim()
  const sl = [...effectiveLink.value.supportSkillLevels]
  sl[slotIdx] = clampSupportLevelForSkillId(el.value, sid)
  emitLink({ supportSkillLevels: sl })
}

function isExclusiveTierSupportSlot(slotIdx: number): boolean {
  const id = (props.modelValue.supportSkillIds[slotIdx] ?? '').trim()
  return id.length > 0 && supportLevelMaxForSkillId(id) === 3
}

function onExclusiveCustomBonusInput(slotIdx: number, e: Event) {
  const el = e.target as HTMLInputElement
  const next = [...effectiveLink.value.supportExclusiveCustomBonuses]
  next[slotIdx] = el.value
  emitLink({ supportExclusiveCustomBonuses: next })
}

const editingSlot = ref<'main' | number | null>('main')
/** 多选标签；空数组表示不筛选（等同「全部」） */
const selectedFilterTags = ref<string[]>([])
/** 技能列表按名称模糊筛选（不区分大小写，子串匹配） */
const pickerSearchQuery = ref('')

const roleLabel = computed(() => {
  if (props.role === 'core') return '核心技能'
  if (props.role === 'active') return '主动技能'
  return '被动技能'
})

const supportCount = computed(
  () => props.modelValue.supportSkillIds.filter(v => (v ?? '').trim().length > 0).length
)

/** 百分比坐标；整体略向内收，避免节点一半高度贴边 */
const supportPoints = [
  { x: 50, y: 16 },
  { x: 18, y: 38 },
  { x: 30, y: 80 },
  { x: 70, y: 80 },
  { x: 82, y: 38 }
]

const mainSkillName = computed(() => {
  const hit = props.mainOptions.find(opt => opt.id === props.modelValue.mainSkillId)
  return hit?.name ?? ''
})

const mainSkillOption = computed(
  () => props.mainOptions.find(opt => opt.id === props.modelValue.mainSkillId) ?? null
)

const POPOVER_WIDTH = 280
/** 与锚点右侧留缝（px），避免浮层压住技能列表导致点不中；移入浮层仍可续接 hover */
const POPOVER_GAP = 10

const detailPopover = ref<{ skill: SkillOption | null; top: number; left: number }>({
  skill: null,
  top: 0,
  left: 0
})

let hidePopoverTimer: ReturnType<typeof setTimeout> | null = null

function cancelHidePopover() {
  if (hidePopoverTimer !== null) {
    clearTimeout(hidePopoverTimer)
    hidePopoverTimer = null
  }
}

function scheduleHidePopover() {
  cancelHidePopover()
  hidePopoverTimer = window.setTimeout(() => {
    detailPopover.value = { skill: null, top: 0, left: 0 }
    hidePopoverTimer = null
  }, 220)
}

function wikiSkillPageUrl(skillId: string): string {
  return `https://tlidb.com/cn/${skillId}`
}

function skillHasSpellTag(opt: SkillOption | null): boolean {
  if (!opt?.tags?.length) return false
  return opt.tags.some(t => (t ?? '').trim() === '法术')
}

/** 法术主动：20 级基础点伤范围（skillBaseDamageByLevel 第 20 档） */
function spellLevel20BaseDamageRange(opt: SkillOption | null): string | null {
  if (!opt || !skillHasSpellTag(opt)) return null
  const arr = opt.skillBaseDamageByLevel
  if (!arr || arr.length < MAIN_LEVEL_MAX) return null
  const s = (arr[MAIN_LEVEL_MAX - 1] ?? '').trim()
  return s.length > 0 ? s : null
}

function forceCloseDetailPopover() {
  cancelHidePopover()
  detailPopover.value = { skill: null, top: 0, left: 0 }
}

function showDetailPopover(skill: SkillOption, anchorEl: HTMLElement) {
  cancelHidePopover()
  const r = anchorEl.getBoundingClientRect()
  let left = r.right + POPOVER_GAP
  let top = r.top
  if (left + POPOVER_WIDTH > window.innerWidth - 8) {
    left = Math.max(8, r.left - POPOVER_WIDTH - POPOVER_GAP)
  }
  const estH = 160
  if (top + estH > window.innerHeight - 8) {
    top = Math.max(8, window.innerHeight - estH - 8)
  }
  detailPopover.value = { skill, top, left }
}

function onPickerSkillEnter(opt: SkillOption, e: MouseEvent | FocusEvent) {
  const el = e.currentTarget
  if (el instanceof HTMLElement) showDetailPopover(opt, el)
}

function onMainNodeDetailEnter(e: MouseEvent) {
  const opt = mainSkillOption.value
  if (!opt) return
  const el = e.currentTarget
  if (el instanceof HTMLElement) showDetailPopover(opt, el)
}

function onSupportNodeDetailEnter(idx: number, e: MouseEvent) {
  const id = props.modelValue.supportSkillIds[idx]
  if (!(id ?? '').trim()) return
  const opt = props.supportOptions.find(o => o.id === id)
  if (!opt) return
  const el = e.currentTarget
  if (el instanceof HTMLElement) showDetailPopover(opt, el)
}

function selectMainEditingSlot() {
  if (editingSlot.value !== 'main') {
    selectedFilterTags.value = []
    pickerSearchQuery.value = ''
  }
  forceCloseDetailPopover()
  editingSlot.value = 'main'
}

function onSupportSlotClick(idx: number) {
  if (!hasMainSkillSelection.value) return
  if (editingSlot.value !== idx) {
    selectedFilterTags.value = []
    pickerSearchQuery.value = ''
  }
  forceCloseDetailPopover()
  editingSlot.value = idx
}

function closeDetailPopoverIfOpen() {
  if (!detailPopover.value.skill) return
  forceCloseDetailPopover()
}

let appMainScrollEl: HTMLElement | null = null

onMounted(() => {
  appMainScrollEl = document.querySelector('.app-main') as HTMLElement | null
  window.addEventListener('wheel', closeDetailPopoverIfOpen, { passive: true, capture: true })
  appMainScrollEl?.addEventListener('scroll', closeDetailPopoverIfOpen, { passive: true })
})

onUnmounted(() => {
  window.removeEventListener('wheel', closeDetailPopoverIfOpen, { capture: true })
  appMainScrollEl?.removeEventListener('scroll', closeDetailPopoverIfOpen)
  appMainScrollEl = null
  cancelHidePopover()
})

const hasMainSkillSelection = computed(
  () => (props.modelValue.mainSkillId ?? '').trim().length > 0
)

const hasAnySkillSelection = computed(
  () =>
    hasMainSkillSelection.value ||
    props.modelValue.supportSkillIds.some(id => (id ?? '').trim().length > 0)
)

function hasSupportSelection(index: number) {
  return (props.modelValue.supportSkillIds[index] ?? '').trim().length > 0
}

function clearMainSkill() {
  emitLink({ mainSkillId: '', mainSkillLevel: DEFAULT_MAIN_SKILL_LEVEL })
}

function clearSupportSkill(index: number) {
  const nextIds = [...props.modelValue.supportSkillIds]
  nextIds[index] = ''
  const nextLevels = [...effectiveLink.value.supportSkillLevels]
  nextLevels[index] = DEFAULT_SUPPORT_SKILL_LEVEL
  const nextCustoms = [...effectiveLink.value.supportExclusiveCustomBonuses]
  nextCustoms[index] = ''
  emitLink({
    supportSkillIds: nextIds,
    supportSkillLevels: nextLevels,
    supportExclusiveCustomBonuses: nextCustoms
  })
}

function clearAllSkills() {
  cancelHidePopover()
  detailPopover.value = { skill: null, top: 0, left: 0 }
  editingSlot.value = null
  emitLink({
    mainSkillId: '',
    supportSkillIds: props.modelValue.supportSkillIds.map(() => ''),
    mainSkillLevel: DEFAULT_MAIN_SKILL_LEVEL,
    supportSkillLevels: [
      DEFAULT_SUPPORT_SKILL_LEVEL,
      DEFAULT_SUPPORT_SKILL_LEVEL,
      DEFAULT_SUPPORT_SKILL_LEVEL,
      DEFAULT_SUPPORT_SKILL_LEVEL,
      DEFAULT_SUPPORT_SKILL_LEVEL
    ],
    supportExclusiveCustomBonuses: ['', '', '', '', '']
  })
}

/** 核心槽已选主技能时，左上角标题显示技能名，否则用传入的 title */
const headerTitle = computed(() => {
  if (props.role === 'core') {
    const n = mainSkillName.value.trim()
    if (n) return n
  }
  return props.title
})

const mainSkillIconUrl = computed(() => {
  const hit = props.mainOptions.find(opt => opt.id === props.modelValue.mainSkillId)
  return (hit?.iconUrl ?? '').trim()
})

const supportSlotsMeta = computed(() =>
  props.modelValue.supportSkillIds.map(skillId => {
    const hit = props.supportOptions.find(opt => opt.id === skillId)
    return {
      name: hit?.name ?? '',
      iconUrl: (hit?.iconUrl ?? '').trim()
    }
  })
)

function supportNodeStyleByIndex(index: number) {
  const p = supportPoints[index]
  return {
    left: `${p.x}%`,
    top: `${p.y}%`
  }
}

const pickerTitle = computed(() => {
  if (editingSlot.value === 'main') return '选择主技能'
  if (typeof editingSlot.value === 'number') return `选择辅助 ${editingSlot.value + 1}`
  return '请选择一个节点'
})

/**
 * 选辅助时：
 * - 普通辅助：与当前主技能至少共有一个标签（主技能无标签时不按标签过滤）。
 * - 崇高 / 华贵：带独立标签「崇高」「华贵」；须先选主技能，且辅助 id 前缀（%3A 前）与主技能 id 一致。
 * - 华贵仅允许装在第 3 辅槽，崇高仅允许第 5 辅槽；已选区用「T 级」T0–T2 与三档增伤（选槽时列表会再过滤）。
 * - 未选主技能时：不列出崇高、华贵专属辅助。
 * 主技能含「光环」时额外允许封印转化、精密 封印转化（二者仅有「辅助」标签，游戏内可连光环）。
 */
const supportOptionsMatchingMainTags = computed(() => {
  const mainId = (props.modelValue.mainSkillId ?? '').trim()

  if (!mainId) {
    return props.supportOptions.filter(sup => !isExclusiveSupportOpt(sup))
  }

  const main = props.mainOptions.find(o => o.id === mainId)
  const mainTags = (main?.tags ?? []).map(t => (t ?? '').trim()).filter(Boolean)
  const mainSet = new Set(mainTags)

  const list = props.supportOptions.filter(sup => {
    if (isExclusiveSupportOpt(sup)) {
      const linked = exclusiveSupportLinkedMainId((sup.id ?? '').trim())
      return linked !== null && linked === mainId
    }
    if (!mainTags.length) return true
    for (const t of sup.tags ?? []) {
      if (mainSet.has((t ?? '').trim())) return true
    }
    return false
  })

  if (!mainSet.has('光环')) {
    return list
  }
  const byId = new Map(list.map(s => [(s.id ?? '').trim(), s]))
  for (const sid of AURA_SUPPORT_LINK_IDS) {
    if (byId.has(sid)) continue
    const sup = props.supportOptions.find(o => (o.id ?? '').trim() === sid)
    if (sup) byId.set(sid, sup)
  }
  return Array.from(byId.values())
})

const currentOptions = computed(() => {
  if (editingSlot.value === 'main') return props.mainOptions
  if (typeof editingSlot.value === 'number') {
    const idx = editingSlot.value
    const base = supportOptionsMatchingMainTags.value
    const usedElsewhere = new Set<string>()
    props.modelValue.supportSkillIds.forEach((id, i) => {
      if (i === idx) return
      const t = (id ?? '').trim()
      if (t) usedElsewhere.add(t)
    })
    return base
      .filter(opt => !usedElsewhere.has((opt.id ?? '').trim()))
      .filter(opt => exclusiveSkillAllowedInSupportSlot(opt, idx))
  }
  return []
})

const effectiveTagWhitelist = computed((): string[] => {
  if (editingSlot.value === 'main') {
    if (props.mainTagWhitelist?.length) return props.mainTagWhitelist
    return props.tagWhitelist ?? []
  }
  if (typeof editingSlot.value === 'number') {
    return props.tagWhitelist ?? []
  }
  return props.tagWhitelist ?? []
})

const availableTags = computed(() => {
  const hit = new Set<string>()
  const wl = effectiveTagWhitelist.value
  const sourceTags = wl.length
    ? wl
    : Array.from(
        new Set(
          currentOptions.value.flatMap(opt =>
            (opt.tags ?? []).map(tag => (tag ?? '').trim()).filter(Boolean)
          )
        )
      )

  for (const opt of currentOptions.value) {
    for (const tag of opt.tags ?? []) {
      const t = (tag ?? '').trim()
      if (t && sourceTags.includes(t)) hit.add(t)
    }
  }
  // 已选标签必须保留在芯片列表中，否则 v-for 不渲染对应按钮，选中态会「消失」
  for (const raw of selectedFilterTags.value) {
    const t = (raw ?? '').trim()
    if (t && sourceTags.includes(t)) hit.add(t)
  }
  return ['全部', ...sourceTags.filter(t => hit.has(t))]
})

const filteredOptions = computed(() => {
  let list = currentOptions.value
  const picked = selectedFilterTags.value
  if (picked.length) {
    list = list.filter(opt => {
      const tags = new Set(
        (opt.tags ?? []).map(t => (t ?? '').trim()).filter(Boolean)
      )
      return picked.every(t => tags.has(t))
    })
  }
  const q = pickerSearchQuery.value.trim().toLowerCase()
  if (q) {
    list = list.filter(opt =>
      (opt.name ?? '').toLowerCase().includes(q)
    )
  }
  return list
})

watch(hasMainSkillSelection, ok => {
  if (!ok && typeof editingSlot.value === 'number') {
    selectedFilterTags.value = []
    pickerSearchQuery.value = ''
    forceCloseDetailPopover()
    editingSlot.value = 'main'
  }
})

function reconcileSupportSkillIdsWithMainAndSlots(): void {
  const cur = props.modelValue.supportSkillIds
  const allowedByMain = new Set(
    supportOptionsMatchingMainTags.value.map(s => (s.id ?? '').trim()).filter(Boolean)
  )
  const next = cur.map((id, i) => {
    const t = (id ?? '').trim()
    if (!t) return ''
    if (!allowedByMain.has(t)) return ''
    const opt = props.supportOptions.find(o => (o.id ?? '').trim() === t)
    if (!opt || !exclusiveSkillAllowedInSupportSlot(opt, i)) return ''
    return t
  })
  const changed = next.some((v, i) => v !== (cur[i] ?? '').trim())
  if (!changed) return
  const nextLevels = [...effectiveLink.value.supportSkillLevels]
  const nextCustoms = [...effectiveLink.value.supportExclusiveCustomBonuses]
  next.forEach((id, i) => {
    if (!(id ?? '').trim()) {
      nextLevels[i] = DEFAULT_SUPPORT_SKILL_LEVEL
      nextCustoms[i] = ''
    }
  })
  emitLink({
    supportSkillIds: next,
    supportSkillLevels: nextLevels,
    supportExclusiveCustomBonuses: nextCustoms
  })
}

watch(
  [
    () => props.modelValue.mainSkillId,
    () =>
      (props.modelValue.supportSkillIds ?? [])
        .map(x => String(x ?? '').trim())
        .join('\x1f')
  ],
  () => {
    reconcileSupportSkillIdsWithMainAndSlots()
  }
)

function isFilterTagActive(tag: string) {
  if (tag === '全部') return selectedFilterTags.value.length === 0
  return selectedFilterTags.value.includes(tag)
}

function onFilterTagClick(tag: string, e?: MouseEvent) {
  if (tag === '全部') {
    selectedFilterTags.value = []
  } else {
    const cur = selectedFilterTags.value
    const i = cur.indexOf(tag)
    if (i >= 0) {
      selectedFilterTags.value = cur.filter(t => t !== tag)
    } else {
      selectedFilterTags.value = [...cur, tag]
    }
  }
  // 避免点击后按钮保持 :focus，鼠标一动焦点环消失被误认为「选中消失」
  const el = e?.currentTarget
  if (el instanceof HTMLButtonElement) {
    el.blur()
  }
}

function applyOption(skillId: string) {
  if (editingSlot.value === 'main') {
    emitLink({ mainSkillId: skillId, mainSkillLevel: DEFAULT_MAIN_SKILL_LEVEL })
    return
  }
  if (typeof editingSlot.value !== 'number') return
  if (!hasMainSkillSelection.value) return
  const sid = skillId.trim()
  const slotIdx = editingSlot.value
  if (
    sid &&
    props.modelValue.supportSkillIds.some(
      (id, i) => i !== slotIdx && (id ?? '').trim() === sid
    )
  ) {
    return
  }
  const next = [...props.modelValue.supportSkillIds]
  next[slotIdx] = skillId
  const picked = props.supportOptions.find(o => o.id === skillId)
  const defaultLv =
    picked?.supportDamageBonusByTier?.length === 3 || isWikiExclusiveSupportSkillId(skillId)
      ? DEFAULT_EXCLUSIVE_TIER_LEVEL
      : DEFAULT_SUPPORT_SKILL_LEVEL
  const sl = [...effectiveLink.value.supportSkillLevels]
  sl[slotIdx] = defaultLv
  const customs = [...effectiveLink.value.supportExclusiveCustomBonuses]
  customs[slotIdx] = ''
  emitLink({
    supportSkillIds: next,
    supportSkillLevels: sl,
    supportExclusiveCustomBonuses: customs
  })
}

function resetPickerFilters() {
  pickerSearchQuery.value = ''
  selectedFilterTags.value = []
}
</script>

<style scoped>
.skill-link-card-root {
  display: flex;
  flex-direction: column;
  min-width: 0;
  min-height: 0;
}

.skill-card {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px;
}

.skill-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.skill-card-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  flex: 1;
}

.skill-card-title {
  font-size: 15px;
  color: #fff;
  font-weight: 600;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.skill-card-role {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.role-core {
  color: #facc15;
  background: rgba(250, 204, 21, 0.14);
  border-color: rgba(250, 204, 21, 0.35);
}

.role-active {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.14);
  border-color: rgba(96, 165, 250, 0.35);
}

.role-passive {
  color: #34d399;
  background: rgba(52, 211, 153, 0.14);
  border-color: rgba(52, 211, 153, 0.35);
}

.skill-card-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.skill-card-split {
  display: grid;
  grid-template-columns: minmax(260px, 1fr) minmax(300px, 440px);
  gap: 14px;
  align-items: start;
  min-width: 0;
}

@media (max-width: 920px) {
  .skill-card-split {
    grid-template-columns: 1fr;
  }
}

.skill-split-left {
  min-width: 0;
}

.skill-split-right {
  min-width: 0;
}

.selection-data-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
  padding: 8px 10px;
  overflow: visible;
}

.selection-data-head {
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
  margin-bottom: 6px;
}

.selection-data-empty {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
  line-height: 1.45;
}

.selection-data-list {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 8px;
  align-items: start;
}

.selection-block--main {
  grid-column: 1 / -1;
}

.selection-block {
  padding: 5px 8px;
  border-radius: 7px;
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  min-width: 0;
}

@media (max-width: 920px) {
  .selection-data-list {
    grid-template-columns: 1fr;
  }

  .selection-block--main {
    grid-column: auto;
  }
}

.selection-block--support {
  background: rgba(96, 165, 250, 0.06);
  border-color: rgba(96, 165, 250, 0.12);
}

.selection-block-title {
  font-size: 9px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: rgba(255, 255, 255, 0.45);
  margin-bottom: 2px;
}

.selection-block-name {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  line-height: 1.25;
  margin-bottom: 4px;
  word-break: break-word;
}

.selection-level-row {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 3px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.75);
}

.selection-level-label {
  flex-shrink: 0;
  min-width: 2.5em;
}

.selection-level-row--support-lv {
  flex-wrap: nowrap;
  min-width: 0;
}

.selection-level-row--support-lv .selection-level-select {
  flex: 1;
  min-width: 0;
  max-width: 110px;
}

.selection-level-row--support-lv:has(.selection-exclusive-value-input) .selection-level-select {
  flex: 0 0 auto;
  max-width: 88px;
  width: auto;
}

.selection-exclusive-value-input {
  flex: 1;
  min-width: 0;
  width: 0;
  height: 26px;
  box-sizing: border-box;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background: rgba(26, 26, 46, 0.95);
  color: rgba(255, 255, 255, 0.92);
  font-size: 11px;
  padding: 0 6px;
  color-scheme: dark;
}

.selection-exclusive-value-input::placeholder {
  color: rgba(255, 255, 255, 0.35);
}

.selection-exclusive-value-input:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.55);
  outline-offset: 2px;
  border-color: rgba(233, 69, 96, 0.5);
}

.selection-level-select {
  flex: 1;
  min-width: 0;
  max-width: 110px;
  height: 26px;
  border-radius: 5px;
  border: 1px solid rgba(255, 255, 255, 0.22);
  background-color: rgba(26, 26, 46, 0.95);
  color: rgba(255, 255, 255, 0.92);
  font-size: 11px;
  padding: 0 6px;
  cursor: pointer;
  /* 提示系统使用深色原生下拉，减轻白底列表 */
  color-scheme: dark;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.06);
}

.selection-level-select:hover:not(:disabled) {
  border-color: rgba(233, 69, 96, 0.42);
  background-color: rgba(30, 30, 52, 0.98);
}

.selection-level-select:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.55);
  outline-offset: 2px;
  border-color: rgba(233, 69, 96, 0.5);
}

.selection-level-select option {
  background-color: #1a1a2e;
  color: rgba(255, 255, 255, 0.92);
}

.selection-level-select:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.selection-stat-lines {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.selection-stat-line {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 11px;
  line-height: 1.3;
}

.selection-stat-k {
  color: rgba(255, 255, 255, 0.5);
  flex-shrink: 0;
}

.selection-stat-v {
  color: rgba(255, 255, 255, 0.92);
  font-variant-numeric: tabular-nums;
  text-align: right;
}

.link-diagram {
  position: relative;
  min-height: 450px;
  height: 450px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: radial-gradient(circle at center, rgba(233, 69, 96, 0.08), rgba(0, 0, 0, 0.2));
  margin-bottom: 10px;
  overflow: hidden;
}

.link-diagram--split {
  margin-bottom: 0;
  /* 固定高度，不因右侧数值区变高而被纵向拉长变形 */
  height: 450px;
  min-height: 450px;
}

.link-diagram-clear-all {
  position: absolute;
  top: 8px;
  right: 8px;
  z-index: 6;
  height: 28px;
  padding: 0 10px;
  border-radius: 7px;
  border: 1px solid rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.2);
  color: rgba(255, 255, 255, 0.95);
  font-size: 12px;
  cursor: pointer;
  transition: background 0.15s ease, border-color 0.15s ease;
}

.link-diagram-clear-all:hover {
  background: rgba(233, 69, 96, 0.35);
  border-color: rgba(233, 69, 96, 0.65);
}

.link-diagram-clear-all:focus-visible {
  outline: 2px solid rgba(255, 255, 255, 0.55);
  outline-offset: 2px;
}

.link-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.node {
  position: absolute;
  transform: translate(-50%, -50%);
  box-sizing: border-box;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(18, 18, 35, 0.95);
  color: #fff;
  cursor: default;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: stretch;
  justify-content: stretch;
  padding: 0;
  text-align: center;
}

.node-body {
  flex: 1;
  min-height: 0;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin: 0;
  border: none;
  background: transparent;
  color: inherit;
  cursor: pointer;
  text-align: center;
  font: inherit;
  position: relative;
  box-sizing: border-box;
}

.node-clear {
  position: absolute;
  top: 3px;
  right: 3px;
  z-index: 4;
  width: 22px;
  height: 22px;
  padding: 0;
  margin: 0;
  border: none;
  border-radius: 6px;
  font-size: 17px;
  font-weight: 600;
  line-height: 1;
  color: #fff;
  background: rgba(233, 69, 96, 0.88);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  pointer-events: none;
  transition: opacity 0.15s ease, background 0.15s ease;
}

.node-clear--support {
  top: 2px;
  right: 2px;
  width: 19px;
  height: 19px;
  font-size: 14px;
  border-radius: 5px;
}

.node.filled:hover .node-clear,
.node.filled:focus-within .node-clear {
  opacity: 1;
  pointer-events: auto;
}

.node-clear:hover {
  background: rgba(220, 50, 80, 1);
}

.node-clear:focus-visible {
  opacity: 1;
  pointer-events: auto;
  outline: 2px solid rgba(255, 255, 255, 0.65);
  outline-offset: 1px;
}

.node:hover {
  border-color: rgba(233, 69, 96, 0.5);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.16);
}

.node.active {
  border-color: rgba(233, 69, 96, 0.8);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.24);
}

.node.filled {
  border-color: rgba(52, 211, 153, 0.55);
}

.node-main {
  left: 50%;
  top: 50%;
  width: 128px;
  height: 128px;
  min-height: 128px;
  z-index: 2;
}

.node-main .node-body {
  gap: 3px;
  padding: 6px;
  min-height: 100%;
}

.node-support {
  width: 96px;
  height: 96px;
  min-height: 96px;
  z-index: 3;
}

.node-support .node-body {
  gap: 2px;
  padding: 5px;
  min-height: 100%;
}

.node-support--locked .node-body:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.node-support--locked:not(.filled) {
  border-color: rgba(255, 255, 255, 0.08);
}

.node-support--locked:not(.filled):hover {
  border-color: rgba(255, 255, 255, 0.12);
  box-shadow: none;
}

.node-slot-badge {
  position: absolute;
  top: 4px;
  left: 4px;
  z-index: 1;
  min-width: 17px;
  height: 17px;
  padding: 0 4px;
  box-sizing: border-box;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 700;
  line-height: 17px;
  text-align: center;
  color: rgba(255, 255, 255, 0.95);
  background: rgba(0, 0, 0, 0.58);
  border: none;
  pointer-events: none;
}

.node-support.active .node-slot-badge {
  background: rgba(233, 69, 96, 0.4);
}

.node-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 9px;
  overflow: hidden;
  flex-shrink: 0;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.node-icon-wrap--support {
  width: 36px;
  height: 36px;
  border-radius: 7px;
  margin-top: 2px;
}

.node-icon-wrap--empty {
  border-style: dashed;
  opacity: 0.65;
}

.node-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.node-name {
  font-size: 12px;
  line-height: 1.25;
  max-width: 100%;
}

.node-main .node-name {
  font-size: 11px;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.node-name--support {
  font-size: 10px;
  line-height: 1.2;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-all;
}

.picker-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
  padding: 10px;
}

.picker-panel--below {
  margin-top: 14px;
  width: 100%;
  min-width: 0;
}

.picker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.picker-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.82);
}

.picker-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-search-row {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
}

.picker-search-input {
  flex: 1;
  min-width: 0;
  height: 32px;
  padding: 0 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(26, 26, 46, 0.92);
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  color-scheme: dark;
  box-sizing: border-box;
}

.picker-search-input::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.picker-search-input:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.45);
  outline-offset: 2px;
  border-color: rgba(233, 69, 96, 0.4);
}

.picker-reset {
  flex-shrink: 0;
  height: 32px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  color: #fff;
  font-size: 12px;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}

.picker-reset:hover:not(:disabled) {
  border-color: rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.12);
}

.picker-reset:disabled {
  opacity: 0.38;
  cursor: not-allowed;
}

.picker-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.03);
  color: #fff;
  border-radius: 999px;
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-chip:hover:not(.active) {
  border-color: rgba(233, 69, 96, 0.5);
}

.tag-chip:focus {
  outline: none;
}

.tag-chip:focus-visible:not(.active) {
  outline: 2px solid rgba(233, 69, 96, 0.45);
  outline-offset: 2px;
}

.tag-chip.active,
.tag-chip.active:hover,
.tag-chip.active:focus,
.tag-chip.active:focus-visible {
  border-color: rgba(233, 69, 96, 0.88);
  background: rgba(233, 69, 96, 0.24);
  color: #fff;
}

.opt-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.opt-chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.03);
  color: #fff;
  border-radius: 10px;
  min-height: 44px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
}

.opt-chip:hover {
  border-color: rgba(233, 69, 96, 0.6);
  background: rgba(233, 69, 96, 0.14);
}

.picker-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 2px 0 4px;
}

.opt-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}

.opt-name {
  line-height: 1.25;
}

.skill-detail-popover {
  position: fixed;
  z-index: 20000;
  width: min(280px, calc(100vw - 16px));
  pointer-events: auto;
}

.skill-detail-popover-inner {
  display: flex;
  gap: 10px;
  padding: 12px;
  background: linear-gradient(145deg, rgba(30, 30, 50, 0.98), rgba(18, 18, 32, 0.99));
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 12px;
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.55), 0 0 0 1px rgba(233, 69, 96, 0.12);
}

.skill-detail-popover-icon-wrap {
  flex-shrink: 0;
  width: 48px;
  height: 48px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.35);
}

.skill-detail-popover-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.skill-detail-popover-body {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skill-detail-popover-name {
  font-size: 14px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
}

.skill-detail-popover-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.skill-detail-popover-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 6px 0 2px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.skill-detail-stat-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
  font-size: 11px;
  line-height: 1.35;
}

.skill-detail-stat-label {
  color: rgba(255, 255, 255, 0.55);
  flex-shrink: 0;
}

.skill-detail-stat-value {
  color: rgba(255, 255, 255, 0.92);
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.skill-detail-stat-value--spell-flat {
  color: rgba(125, 211, 252, 0.98);
  font-weight: 600;
}

.skill-detail-tag {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(255, 255, 255, 0.12);
  color: rgba(255, 255, 255, 0.82);
}

.skill-detail-wiki {
  font-size: 11px;
  color: rgba(233, 69, 96, 0.95);
  text-decoration: none;
  margin-top: 2px;
  align-self: flex-start;
}

.skill-detail-wiki:hover {
  text-decoration: underline;
}
</style>

