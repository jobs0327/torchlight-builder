<template>
  <div class="skills-page">
    <div class="skills-header">
      <h1>技能模块</h1>
      <p>
        当前 BD 技能构成：<strong>1 个核心技能 + 4 个主动技能 + 4 个被动技能</strong>，每个技能可连接
        <strong>5 个辅助技能</strong>。
      </p>
    </div>

    <div class="skills-summary">
      <div class="summary-item">
        <span class="summary-label">技能位总数</span>
        <span class="summary-value">9</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">已选择技能</span>
        <span class="summary-value">{{ selectedMainCount }}/9</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">已连接辅助</span>
        <span class="summary-value">{{ selectedSupportCount }}/45</span>
      </div>
    </div>

    <div class="skills-layout">
      <aside class="skills-left">
        <section class="slot-section">
          <h2>核心技能</h2>
          <button
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'core' }"
            @click="selectSlot('core', 0)"
          >
            <span
              class="slot-icon-wrap"
              :class="{ 'slot-icon-wrap--empty': !coreSidebarIconUrl }"
            >
              <img
                v-if="coreSidebarIconUrl"
                :src="coreSidebarIconUrl"
                alt=""
                class="slot-icon-img"
                loading="lazy"
              />
              <svg
                v-else
                class="slot-icon-placeholder-svg"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="5"
                  stroke="currentColor"
                  stroke-width="1.25"
                  stroke-dasharray="3 2.5"
                  opacity="0.4"
                />
                <path
                  d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-1.5 1.8-2 2.7V13M12 16.2h.01"
                  stroke="currentColor"
                  stroke-width="1.35"
                  stroke-linecap="round"
                  opacity="0.5"
                />
              </svg>
            </span>
            <span class="slot-item-text">
              <span class="slot-title">核心技能槽位</span>
              <span class="slot-name">{{
                getSkillDisplayName(coreSkill.mainSkillId, activeSkillOptions) || '未选择'
              }}</span>
            </span>
          </button>
        </section>

        <section class="slot-section">
          <h2>主动技能</h2>
          <button
            v-for="(item, idx) in activeSkills"
            :key="`active-list-${idx}`"
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'active' && selectedSlot.index === idx }"
            @click="selectSlot('active', idx)"
          >
            <span
              class="slot-icon-wrap"
              :class="{ 'slot-icon-wrap--empty': !getSkillIconUrl(item.mainSkillId, activeSkillOptions) }"
            >
              <img
                v-if="getSkillIconUrl(item.mainSkillId, activeSkillOptions)"
                :src="getSkillIconUrl(item.mainSkillId, activeSkillOptions)"
                alt=""
                class="slot-icon-img"
                loading="lazy"
              />
              <svg
                v-else
                class="slot-icon-placeholder-svg"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="5"
                  stroke="currentColor"
                  stroke-width="1.25"
                  stroke-dasharray="3 2.5"
                  opacity="0.4"
                />
                <path
                  d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-1.5 1.8-2 2.7V13M12 16.2h.01"
                  stroke="currentColor"
                  stroke-width="1.35"
                  stroke-linecap="round"
                  opacity="0.5"
                />
              </svg>
            </span>
            <span class="slot-item-text">
              <span class="slot-title">主动技能 {{ idx + 1 }}</span>
              <span class="slot-name">{{
                getSkillDisplayName(item.mainSkillId, activeSkillOptions) || '未选择'
              }}</span>
            </span>
          </button>
        </section>

        <section class="slot-section">
          <h2>被动技能</h2>
          <button
            v-for="(item, idx) in passiveSkills"
            :key="`passive-list-${idx}`"
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'passive' && selectedSlot.index === idx }"
            @click="selectSlot('passive', idx)"
          >
            <span
              class="slot-icon-wrap"
              :class="{ 'slot-icon-wrap--empty': !getSkillIconUrl(item.mainSkillId, passiveSkillOptions) }"
            >
              <img
                v-if="getSkillIconUrl(item.mainSkillId, passiveSkillOptions)"
                :src="getSkillIconUrl(item.mainSkillId, passiveSkillOptions)"
                alt=""
                class="slot-icon-img"
                loading="lazy"
              />
              <svg
                v-else
                class="slot-icon-placeholder-svg"
                viewBox="0 0 24 24"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="5"
                  stroke="currentColor"
                  stroke-width="1.25"
                  stroke-dasharray="3 2.5"
                  opacity="0.4"
                />
                <path
                  d="M9.5 9.5a2.5 2.5 0 0 1 5 0c0 1.5-1.5 1.8-2 2.7V13M12 16.2h.01"
                  stroke="currentColor"
                  stroke-width="1.35"
                  stroke-linecap="round"
                  opacity="0.5"
                />
              </svg>
            </span>
            <span class="slot-item-text">
              <span class="slot-title">被动技能 {{ idx + 1 }}</span>
              <span class="slot-name">{{
                getSkillDisplayName(item.mainSkillId, passiveSkillOptions) || '未选择'
              }}</span>
            </span>
          </button>
        </section>
      </aside>

      <section class="skills-right">
        <h2 class="panel-title">{{ selectedPanelTitle }}</h2>

        <SkillLinkCard
          v-if="selectedSlot.role === 'core'"
          title="核心技能"
          role="core"
          :model-value="coreSkill"
          @update:model-value="coreSkill = $event"
          :main-options="activeSkillOptions"
          :support-options="supportSkillOptions"
          :tag-whitelist="supportSkillTags"
          :main-tag-whitelist="activeSkillTags"
        />

        <SkillLinkCard
          v-else-if="selectedSlot.role === 'active'"
          :title="`主动技能 ${selectedSlot.index + 1}`"
          role="active"
          :model-value="activeSkills[selectedSlot.index]"
          @update:model-value="activeSkills[selectedSlot.index] = $event"
          :main-options="activeSkillOptions"
          :support-options="supportSkillOptions"
          :tag-whitelist="supportSkillTags"
          :main-tag-whitelist="activeSkillTags"
        />

        <SkillLinkCard
          v-else
          :title="`被动技能 ${selectedSlot.index + 1}`"
          role="passive"
          :model-value="passiveSkills[selectedSlot.index]"
          @update:model-value="passiveSkills[selectedSlot.index] = $event"
          :main-options="passiveSkillOptions"
          :support-options="supportSkillOptions"
          :tag-whitelist="supportSkillTags"
          :main-tag-whitelist="passiveMainTagWhitelist"
        />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import SkillLinkCard from '@/components/skills/SkillLinkCard.vue'
import activeSkillTagsData from '@/data/skills/activeSkillTags.json'
// 数据由 sync_support_skill_tags.py 从 tlidb 生成
import supportSkillTagsData from '@/data/skills/supportSkillTags.json'
// sync_noble_support_skill_tags.py / sync_magnificent_support_skill_tags.py
import nobleSupportSkillTagsData from '@/data/skills/nobleSupportSkillTags.json'
import magnificentSupportSkillTagsData from '@/data/skills/magnificentSupportSkillTags.json'
// 数据由 sync_passive_skill_tags.py 从 tlidb 生成
import passiveSkillTagsData from '@/data/skills/passiveSkillTags.json'

type SkillStatRow = { label: string; value: string }

type SkillOption = {
  id: string
  name: string
  iconUrl?: string
  tags?: string[]
  statRows?: SkillStatRow[]
  /** 主动 1–20 级伤害倍率展示值 */
  damageMultiplierByLevel?: string[]
  /** 主动 1–20 级技能基础伤害（法术 flat 等，与倍率列对应；纯武器技能通常无此字段） */
  skillBaseDamageByLevel?: string[]
  /** 辅助 1–40 级「所连技能额外伤害」数值展示 */
  supportDamageBonusByLevel?: string[]
  /** 崇高/华贵：T0–T2 三档增伤（与 wiki Tier 0/1/2 一致） */
  supportDamageBonusByTier?: string[]
}

type SkillLinkItem = {
  mainSkillId: string
  supportSkillIds: string[]
  /** 主技能等级 1–20（无成长数据时仍可存，用于 UI） */
  mainSkillLevel?: number
  /** 各辅槽等级 1–40 */
  supportSkillLevels?: number[]
  /** 崇高/华贵 T 级槽自定义增伤展示（与辅槽一一对应） */
  supportExclusiveCustomBonuses?: string[]
}

type SlotRole = 'core' | 'active' | 'passive'

function mergeUniqueStrings(lists: string[][]): string[] {
  const seen = new Set<string>()
  const out: string[] = []
  for (const list of lists) {
    for (const raw of list) {
      const t = String(raw ?? '').trim()
      if (!t || seen.has(t)) continue
      seen.add(t)
      out.push(t)
    }
  }
  return out
}

/** 与 SkillLinkCard 中专属辅助筛选一致（用于标签筛选条） */
const EXCLUSIVE_NOBLE_SUPPORT_TAG = '崇高'
const EXCLUSIVE_MAGNIFICENT_SUPPORT_TAG = '华贵'

const activeSkillTags: string[] = activeSkillTagsData.tags ?? []
const supportSkillTags: string[] = mergeUniqueStrings([
  supportSkillTagsData.tags ?? [],
  nobleSupportSkillTagsData.tags ?? [],
  magnificentSupportSkillTagsData.tags ?? [],
  [EXCLUSIVE_NOBLE_SUPPORT_TAG, EXCLUSIVE_MAGNIFICENT_SUPPORT_TAG]
])
const passiveSkillTags: string[] = passiveSkillTagsData.tags ?? []

function normalizeStatRows(item: unknown): SkillStatRow[] | undefined {
  if (!item || typeof item !== 'object') return undefined
  const raw = (item as { statRows?: unknown }).statRows
  if (!Array.isArray(raw) || raw.length === 0) return undefined
  const rows: SkillStatRow[] = []
  for (const r of raw) {
    if (!r || typeof r !== 'object') continue
    const label = String((r as { label?: unknown }).label ?? '').trim()
    const value = String((r as { value?: unknown }).value ?? '').trim()
    if (label && value) rows.push({ label, value })
  }
  return rows.length ? rows : undefined
}

function normalizeLevelStringArray(
  item: unknown,
  key:
    | 'damageMultiplierByLevel'
    | 'skillBaseDamageByLevel'
    | 'supportDamageBonusByLevel',
  expectedLen: number
): string[] | undefined {
  if (!item || typeof item !== 'object') return undefined
  const raw = (item as Record<string, unknown>)[key]
  if (!Array.isArray(raw) || raw.length !== expectedLen) return undefined
  const out: string[] = []
  for (const v of raw) {
    out.push(String(v ?? '').trim())
  }
  if (key === 'skillBaseDamageByLevel') {
    return out.some(s => s.length > 0) ? out : undefined
  }
  for (const s of out) {
    if (!s) return undefined
  }
  return out
}

function normalizeSupportDamageBonusByTier(item: unknown): string[] | undefined {
  if (!item || typeof item !== 'object') return undefined
  const raw = (item as Record<string, unknown>).supportDamageBonusByTier
  if (!Array.isArray(raw) || raw.length !== 3) return undefined
  const out: string[] = []
  for (const v of raw) {
    out.push(String(v ?? '').trim())
  }
  if (out.some(s => !s)) return undefined
  return out
}

const activeSkillOptionsFromData: SkillOption[] = (activeSkillTagsData.activeSkills ?? []).map(item => ({
  id: String(item.id ?? ''),
  name: String(item.name ?? ''),
  iconUrl: item.localIconUrl ? String(item.localIconUrl) : item.iconUrl ? String(item.iconUrl) : '',
  tags: Array.isArray(item.tags) ? item.tags.map(tag => String(tag)) : [],
  statRows: normalizeStatRows(item),
  damageMultiplierByLevel: normalizeLevelStringArray(item, 'damageMultiplierByLevel', 20),
  skillBaseDamageByLevel: normalizeLevelStringArray(item, 'skillBaseDamageByLevel', 20)
}))

function mapSupportJsonToOptions(rawList: unknown, extraTags: string[] = []): SkillOption[] {
  if (!Array.isArray(rawList)) return []
  const extra = extraTags.map(t => String(t).trim()).filter(Boolean)
  return rawList.map(item => {
    const baseTags = Array.isArray((item as { tags?: unknown }).tags)
      ? (item as { tags: unknown[] }).tags.map(tag => String(tag).trim()).filter(Boolean)
      : []
    const tagSet = new Set<string>([...baseTags, ...extra])
    return {
      id: String((item as { id?: unknown }).id ?? ''),
      name: String((item as { name?: unknown }).name ?? ''),
      iconUrl: (item as { localIconUrl?: unknown; iconUrl?: unknown }).localIconUrl
        ? String((item as { localIconUrl?: unknown }).localIconUrl)
        : (item as { iconUrl?: unknown }).iconUrl
          ? String((item as { iconUrl?: unknown }).iconUrl)
          : '',
      tags: [...tagSet],
      statRows: normalizeStatRows(item),
      supportDamageBonusByLevel: normalizeLevelStringArray(
        item,
        'supportDamageBonusByLevel',
        40
      ),
      supportDamageBonusByTier: normalizeSupportDamageBonusByTier(item)
    }
  })
}

const supportSkillOptionsFromData: SkillOption[] = [
  ...mapSupportJsonToOptions(supportSkillTagsData.supportSkills),
  ...mapSupportJsonToOptions(nobleSupportSkillTagsData.supportSkills, [
    EXCLUSIVE_NOBLE_SUPPORT_TAG
  ]),
  ...mapSupportJsonToOptions(magnificentSupportSkillTagsData.supportSkills, [
    EXCLUSIVE_MAGNIFICENT_SUPPORT_TAG
  ])
]

const passiveSkillOptionsFromData: SkillOption[] = (passiveSkillTagsData.passiveSkills ?? []).map(item => ({
  id: String(item.id ?? ''),
  name: String(item.name ?? ''),
  iconUrl: item.localIconUrl ? String(item.localIconUrl) : item.iconUrl ? String(item.iconUrl) : '',
  tags: Array.isArray(item.tags) ? item.tags.map(tag => String(tag)) : [],
  statRows: normalizeStatRows(item),
  damageMultiplierByLevel: normalizeLevelStringArray(item, 'damageMultiplierByLevel', 20),
  skillBaseDamageByLevel: normalizeLevelStringArray(item, 'skillBaseDamageByLevel', 20)
}))

function createEmptySkillLink(): SkillLinkItem {
  return {
    mainSkillId: '',
    supportSkillIds: ['', '', '', '', ''],
    mainSkillLevel: 20,
    supportSkillLevels: [20, 20, 20, 20, 20],
    supportExclusiveCustomBonuses: ['', '', '', '', '']
  }
}

const coreSkill = ref<SkillLinkItem>(createEmptySkillLink())
const activeSkills = ref<SkillLinkItem[]>(Array.from({ length: 4 }, createEmptySkillLink))
const passiveSkills = ref<SkillLinkItem[]>(Array.from({ length: 4 }, createEmptySkillLink))
const selectedSlot = ref<{ role: SlotRole; index: number }>({ role: 'core', index: 0 })

const activeSkillOptions: SkillOption[] = activeSkillOptionsFromData
const supportSkillOptions: SkillOption[] = supportSkillOptionsFromData

const passiveSkillOptions: SkillOption[] = passiveSkillOptionsFromData
/** 被动主技能 Tag 筛选与 tlidb 列表一致 */
const passiveMainTagWhitelist: string[] = passiveSkillTags

const allSkillNodes = computed(() => [coreSkill.value, ...activeSkills.value, ...passiveSkills.value])

const selectedMainCount = computed(
  () => allSkillNodes.value.filter(item => item.mainSkillId.trim().length > 0).length
)

const selectedSupportCount = computed(() =>
  allSkillNodes.value.reduce(
    (sum, item) => sum + item.supportSkillIds.filter(v => v.trim().length > 0).length,
    0
  )
)

const selectedPanelTitle = computed(() => {
  if (selectedSlot.value.role === 'core') return '核心技能详情'
  if (selectedSlot.value.role === 'active') return `主动技能 ${selectedSlot.value.index + 1} 详情`
  return `被动技能 ${selectedSlot.value.index + 1} 详情`
})

function selectSlot(role: SlotRole, index: number) {
  selectedSlot.value = { role, index }
}

function getSkillDisplayName(skillId: string, options: SkillOption[]) {
  const hit = options.find(o => o.id === skillId)
  return hit?.name ?? ''
}

function getSkillIconUrl(skillId: string, options: SkillOption[]): string {
  const id = (skillId ?? '').trim()
  if (!id) return ''
  const hit = options.find(o => o.id === id)
  return (hit?.iconUrl ?? '').trim()
}

const coreSidebarIconUrl = computed(() => getSkillIconUrl(coreSkill.value.mainSkillId, activeSkillOptions))
</script>

<style scoped>
.skills-page {
  padding: 18px;
  color: #fff;
}

.skills-header {
  margin-bottom: 14px;
}

.skills-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.skills-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.74);
}

.skills-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.summary-item {
  background: rgba(0, 0, 0, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.72);
}

.summary-value {
  font-size: 16px;
  font-weight: 700;
  color: #e94560;
}

.skills-layout {
  display: grid;
  grid-template-columns: 170px minmax(0, 1fr);
  gap: 12px;
}

.skills-left {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.22);
  padding: 8px;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
  min-width: 0;
}

.slot-section + .slot-section {
  margin-top: 12px;
}

.slot-section h2 {
  margin: 0 0 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
}

.slot-item {
  width: 100%;
  text-align: left;
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  padding: 6px 6px;
  color: #fff;
  cursor: pointer;
}

.slot-icon-wrap {
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  border-radius: 7px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.slot-icon-wrap--empty {
  border-style: dashed;
  color: rgba(255, 255, 255, 0.38);
}

.slot-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.slot-icon-placeholder-svg {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.slot-item-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
  text-align: left;
}

.slot-item + .slot-item {
  margin-top: 8px;
}

.slot-item:hover {
  border-color: rgba(233, 69, 96, 0.4);
}

.slot-item.active {
  border-color: rgba(233, 69, 96, 0.8);
  box-shadow: inset 0 0 0 1px rgba(233, 69, 96, 0.22);
  background: rgba(233, 69, 96, 0.08);
}

.slot-item-text .slot-title {
  font-size: 11px;
  line-height: 1.25;
}

.slot-item-text .slot-name {
  font-size: 10px;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.7);
  word-break: break-word;
}

.skills-right {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
  padding: 10px;
}

.panel-title {
  margin: 0 0 10px;
  font-size: 15px;
  color: #f3f4f6;
}

@media (max-width: 1100px) {
  .skills-summary {
    grid-template-columns: 1fr;
  }

  .skills-layout {
    grid-template-columns: 1fr;
  }

  .skills-left {
    max-height: none;
  }
}
</style>
