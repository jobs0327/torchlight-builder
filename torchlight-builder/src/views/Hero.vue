<template>
  <div class="hero-page">
    <ConfirmDialog
      v-model="showSwitchHeroConfirm"
      title="切换英雄"
      :message="switchHeroConfirmMessage"
      cancel-text="取消"
      confirm-text="继续切换"
      @confirm="onConfirmSwitchHero"
      @cancel="onCancelSwitchHero"
    />
    <div class="hero-sidebar">
      <div class="hero-sidebar-header">
        <div>
          <h2>英雄列表</h2>
          <div class="hero-sidebar-count">{{ heroes.length }}</div>
        </div>
        <div class="hero-sidebar-tip">点击左侧查看英雄特性</div>
      </div>

      <div class="hero-list">
        <button
          v-for="hero in heroes"
          :key="hero.id"
          class="hero-item"
          :class="{ active: hero.id === activeHeroId }"
          @click="requestSwitchHero(hero.id)"
        >
          <div class="hero-portrait">
            <img v-if="hero.portrait" :src="hero.portrait" :alt="hero.displayName" />
            <div v-else class="hero-portrait-fallback" />
          </div>
          <div class="hero-meta">
            <div class="hero-name">{{ hero.displayName }}</div>
            <div class="hero-desc">{{ hero.shortDesc }}</div>
          </div>
        </button>
      </div>
    </div>

    <div class="hero-detail">
      <div v-if="activeHero" class="hero-detail-card">
        <div class="hero-detail-header">
          <div class="hero-detail-title">{{ activeHero.traitTitle }}</div>
          <div class="hero-detail-sub" v-if="activeHero.heroName">{{ activeHero.heroName }}</div>
          <div class="hero-detail-desc" v-if="activeHero.heroDescription">{{ activeHero.heroDescription }}</div>
        </div>

        <div class="hero-traits-actions">
          <button
            type="button"
            class="traits-action-btn"
            :class="{ selected: allTraitsCollapsed }"
            @click.stop="onCollapseAllTraits"
            :disabled="!activeHero"
          >
            全部收起
          </button>
          <button
            type="button"
            class="traits-action-btn"
            :class="{ selected: allTraitsExpanded }"
            @click.stop="onExpandAllTraits"
            :disabled="!activeHero"
          >
            全部展开
          </button>
        </div>

        <div class="hero-traits">
          <div
            v-for="t in activeHero.traits"
            :key="t.name"
            class="trait-card"
            :class="{ 'trait-card-selected': isTraitSelected(t) }"
          >
            <div class="trait-head">
              <div class="trait-left">
                <div v-if="t.icon" class="trait-icon">
                  <img :src="t.icon" :alt="t.name" />
                </div>
                <div class="trait-name">{{ t.name }}</div>
              </div>
              <div class="trait-right">
                <div class="trait-level">需求等级 {{ t.requiredLevel }}</div>
                <button
                  type="button"
                  class="trait-expand-btn"
                  :title="isTraitExpanded(t) ? '收起详情' : '展开详情'"
                  :aria-expanded="isTraitExpanded(t)"
                  @click.stop="onToggleTraitExpanded(t)"
                >
                  {{ isTraitExpanded(t) ? '▲' : '▼' }}
                </button>
                <button
                  type="button"
                  class="trait-select-btn"
                  :class="{ selected: isTraitSelected(t) }"
                  :title="isTraitSelected(t) ? '取消选中' : '选中该特性'"
                  @click.stop="onToggleTrait(t)"
                >
                  ✓
                </button>
              </div>
            </div>
            <div v-if="isTraitExpanded(t)" class="trait-effects">
              <div v-for="(e, idx) in t.effects" :key="idx" class="trait-effect">
                {{ e }}
              </div>
            </div>
          </div>
        </div>

        <!-- 英雄专属数值总结：置于特性列表下方 -->
        <div v-if="heroSummaryComponent" class="hero-summary">
          <component :is="heroSummaryComponent" v-bind="heroSummaryProps" />
        </div>

      </div>

      <div v-else class="hero-empty">
        <div class="hero-empty-title">暂无英雄数据</div>
        <div class="hero-empty-tip">请先运行爬虫与数据生成脚本生成 `src/data/heroes.json`</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { useBuildStore } from '@/stores/build'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import { heroSummaryMap } from '@/components/hero/heroSummaryRegistry'
// 数据由爬虫生成：build_hero_data.py -> src/data/heroes/heroes.json
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import heroesJson from '@/data/heroes/heroes.json'

type HeroTrait = {
  name: string
  requiredLevel: number
  effects: string[]
  icon?: string
}

type HeroEntry = {
  id: string
  slug: string
  portrait: string
  displayName: string
  shortDesc: string
  traitTitle: string
  heroName: string
  heroDescription: string
  traits: HeroTrait[]
  sourceUrl: string
}

const heroes = ref<HeroEntry[]>((heroesJson as HeroEntry[]) || [])
const activeHeroId = ref<string>(heroes.value[0]?.id ?? '')

const activeHero = computed(() => heroes.value.find(h => h.id === activeHeroId.value) || null)

const showSwitchHeroConfirm = ref(false)
const pendingHeroId = ref<string | null>(null)

const pendingTargetHero = computed(() =>
  pendingHeroId.value ? heroes.value.find(h => h.id === pendingHeroId.value) ?? null : null
)

const switchHeroConfirmMessage = computed(() => {
  const cur = activeHero.value?.displayName ?? '当前英雄'
  const next = pendingTargetHero.value?.displayName ?? '目标英雄'
  return `「${cur}」已选择特性，切换到「${next}」将清空已选特性，是否继续？`
})

// 交互：按需求等级互斥选择（同 requiredLevel 只能选 1 个特性）
const selectedTraitByRequiredLevel = ref<Record<number, string>>({})
const expandedTraitByName = ref<Record<string, boolean>>({})

const buildStore = useBuildStore()
const HERO_SNAPSHOT_V = 1
const applyingHeroFromStore = ref(false)

function applyHeroFromStore() {
  const raw = buildStore.snapshot.hero
  if (!raw || typeof raw !== 'object') return
  const h = raw as Record<string, unknown>
  if (h.v !== HERO_SNAPSHOT_V) return
  applyingHeroFromStore.value = true
  try {
    if (typeof h.activeHeroId === 'string' && heroes.value.some(x => x.id === h.activeHeroId)) {
      activeHeroId.value = h.activeHeroId
    }
    if (h.selectedTraitByRequiredLevel && typeof h.selectedTraitByRequiredLevel === 'object') {
      const m = h.selectedTraitByRequiredLevel as Record<string, string>
      const next: Record<number, string> = {}
      for (const [k, v] of Object.entries(m)) {
        const num = Number(k)
        if (!Number.isNaN(num) && typeof v === 'string') next[num] = v
      }
      selectedTraitByRequiredLevel.value = next
    }
    if (h.expandedTraitByName && typeof h.expandedTraitByName === 'object') {
      expandedTraitByName.value = { ...(h.expandedTraitByName as Record<string, boolean>) }
    }
  } finally {
    applyingHeroFromStore.value = false
  }
}

applyHeroFromStore()

function hasAnyTraitSelection(): boolean {
  return Object.keys(selectedTraitByRequiredLevel.value).length > 0
}

/** 切换英雄；若已选特性则弹出项目内确认框 */
function requestSwitchHero(nextId: string) {
  if (!nextId || nextId === activeHeroId.value) return
  if (hasAnyTraitSelection()) {
    pendingHeroId.value = nextId
    showSwitchHeroConfirm.value = true
    return
  }
  activeHeroId.value = nextId
}

function onConfirmSwitchHero() {
  const id = pendingHeroId.value
  pendingHeroId.value = null
  if (id) activeHeroId.value = id
}

function onCancelSwitchHero() {
  pendingHeroId.value = null
}

function isTraitSelected(t: HeroTrait) {
  return selectedTraitByRequiredLevel.value[t.requiredLevel] === t.name
}

function onToggleTrait(t: HeroTrait) {
  const lvl = t.requiredLevel
  if (selectedTraitByRequiredLevel.value[lvl] === t.name) {
    delete selectedTraitByRequiredLevel.value[lvl]
    return
  }
  selectedTraitByRequiredLevel.value[lvl] = t.name
}

function isTraitExpanded(t: HeroTrait) {
  return expandedTraitByName.value[t.name] === true
}

function onToggleTraitExpanded(t: HeroTrait) {
  const key = t.name
  expandedTraitByName.value[key] = !isTraitExpanded(t)
}

function onExpandAllTraits() {
  if (!activeHero.value) return
  const map: Record<string, boolean> = {}
  for (const t of activeHero.value.traits || []) {
    map[t.name] = true
  }
  expandedTraitByName.value = map
}

function onCollapseAllTraits() {
  expandedTraitByName.value = {}
}

const allTraitsExpanded = computed(() => {
  if (!activeHero.value) return false
  const list = activeHero.value.traits || []
  if (!list.length) return false
  return list.every(t => expandedTraitByName.value[t.name] === true)
})

const allTraitsCollapsed = computed(() => {
  if (!activeHero.value) return false
  const list = activeHero.value.traits || []
  if (!list.length) return true
  return list.every(t => !expandedTraitByName.value[t.name])
})

watch(
  () => activeHeroId.value,
  () => {
    if (applyingHeroFromStore.value) return
    // 切换英雄时重置选择，避免跨英雄保留错误状态
    selectedTraitByRequiredLevel.value = {}
    expandedTraitByName.value = {}
  }
)

watch(
  [activeHeroId, selectedTraitByRequiredLevel, expandedTraitByName],
  () => {
    if (applyingHeroFromStore.value) return
    buildStore.setHero({
      v: HERO_SNAPSHOT_V,
      activeHeroId: activeHeroId.value,
      selectedTraitByRequiredLevel: { ...selectedTraitByRequiredLevel.value },
      expandedTraitByName: { ...expandedTraitByName.value }
    })
  },
  { deep: true }
)

onMounted(applyHeroFromStore)
onActivated(applyHeroFromStore)

const heroSummaryComponent = computed(() => {
  const id = activeHero.value?.id
  return id ? heroSummaryMap[id] ?? null : null
})

const selectedTraitNames = computed(() =>
  Object.values(selectedTraitByRequiredLevel.value)
    .map(v => (v ?? '').trim())
    .filter(Boolean)
)

const heroSummaryProps = computed<Record<string, unknown>>(() => {
  if (!heroSummaryComponent.value) return {}
  return { selectedTraits: selectedTraitNames.value }
})
</script>

<style>
.hero-page {
  height: 100%;
  display: flex;
  background: #0f0f1a;
}

.hero-sidebar {
  width: 360px;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(0, 0, 0, 0.25);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.hero-sidebar-header {
  padding: 14px 14px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-sidebar-header h2 {
  margin: 0;
  color: #fff;
  font-size: 16px;
  display: inline-block;
  vertical-align: baseline;
}

.hero-sidebar-header .hero-sidebar-count {
  display: inline-block;
  margin-left: 8px;
  font-size: 14px; /* 比 h2 小点 */
  font-weight: 400;
  line-height: 1;
  color: rgba(255, 255, 255, 0.65);
  vertical-align: baseline;
  white-space: nowrap;
}

.hero-sidebar-header .hero-sidebar-count::before {
  content: '(';
}

.hero-sidebar-header .hero-sidebar-count::after {
  content: ')';
}

.hero-sidebar-tip {
  margin-top: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}

.hero-list {
  padding: 10px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: auto;
}

.hero-item {
  display: flex;
  gap: 10px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.18s ease;
  text-align: left;
  color: inherit;
}

.hero-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.hero-item.active {
  border-color: rgba(233, 69, 96, 0.55);
  background: rgba(233, 69, 96, 0.14);
}

.hero-portrait {
  width: 64px;
  height: 64px;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.35);
  flex: 0 0 64px;
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-portrait img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.hero-portrait-fallback {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.08), rgba(255, 255, 255, 0.02));
}

.hero-meta {
  flex: 1;
  min-width: 0;
}

.hero-name {
  color: #fff;
  font-size: 13px;
  font-weight: 600;
}

.hero-desc {
  margin-top: 4px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  line-height: 1.35;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.hero-detail {
  flex: 1;
  overflow: auto;
  padding: 18px 18px 24px;
}

.hero-detail-card {
  max-width: 980px;
  margin: 0 auto;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 14px;
  overflow: hidden;
}

.hero-detail-header {
  padding: 16px 16px 12px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-detail-title {
  color: #fff;
  font-size: 18px;
  font-weight: 700;
}

.hero-detail-sub {
  margin-top: 6px;
  color: rgba(255, 255, 255, 0.75);
  font-size: 13px;
}

.hero-detail-desc {
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
  white-space: pre-wrap;
  line-height: 1.5;
}

.hero-traits {
  padding: 14px;
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
}

.hero-summary {
  padding: 14px 14px 16px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  background: rgba(255, 255, 255, 0.02);
}

.hero-summary-title {
  font-size: 13px;
  font-weight: 600;
  color: #fff;
  margin-bottom: 6px;
}

.hero-summary-line {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 6px;
}

.hero-summary-form {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 6px;
}

.summary-field {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.summary-field input,
.summary-field select {
  height: 22px;
  padding: 0 4px;
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(0, 0, 0, 0.5);
  color: #fff;
  font-size: 12px;
}

.hero-summary-result {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 4px;
}

.hero-summary-highlight {
  color: #ffcc66;
  font-weight: 600;
  margin-left: 4px;
}

.hero-summary-note {
  display: block;
  margin-top: 2px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
}

.trait-card {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 12px;
  padding: 12px;
}

.hero-traits-actions {
  display: flex;
  gap: 10px;
  padding: 8px 14px 0; /* 与下面 hero-traits 的左右 padding 对齐 */
}

.traits-action-btn {
  flex: 0 0 auto;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.18);
  color: rgba(255, 255, 255, 0.72);
  padding: 8px 12px;
  cursor: pointer;
  transition: all 0.16s ease;
  font-size: 12px;
}

.traits-action-btn:hover:not(:disabled) {
  border-color: rgba(233, 69, 96, 0.35);
  color: rgba(255, 255, 255, 0.95);
  background: rgba(233, 69, 96, 0.12);
  box-shadow: 0 0 0 1px rgba(233, 69, 96, 0.25), 0 10px 25px rgba(233, 69, 96, 0.16);
}

.traits-action-btn.selected {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.18);
  color: #fff;
  box-shadow: 0 0 0 1px rgba(233, 69, 96, 0.35), 0 10px 30px rgba(233, 69, 96, 0.16);
}

.traits-action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.trait-card-selected {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.16);
  box-shadow: 0 0 0 1px rgba(233, 69, 96, 0.25), 0 10px 30px rgba(233, 69, 96, 0.12);
}

.trait-head {
  display: flex;
  justify-content: space-between;
  gap: 12px;
  align-items: center;
}

.trait-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.trait-select-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.25);
  color: rgba(255, 255, 255, 0.55);
  cursor: pointer;
  transition: all 0.16s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  line-height: 1;
  padding: 0;
}

.trait-select-btn:hover {
  border-color: rgba(233, 69, 96, 0.35);
  color: rgba(255, 255, 255, 0.8);
}

.trait-select-btn.selected {
  border-color: rgba(233, 69, 96, 0.65);
  background: rgba(233, 69, 96, 0.18);
  color: #fff;
}

.trait-expand-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.18);
  color: rgba(255, 255, 255, 0.6);
  cursor: pointer;
  transition: all 0.16s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  line-height: 1;
  padding: 0;
}

.trait-expand-btn:hover {
  border-color: rgba(233, 69, 96, 0.35);
  color: rgba(255, 255, 255, 0.85);
}

.trait-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.trait-icon {
  width: 32px;
  height: 32px;
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.35);
  flex-shrink: 0;
}

.trait-icon img {
  width: 100%;
  height: 100%;
  display: block;
  object-fit: cover;
}

.trait-name {
  color: #fff;
  font-weight: 700;
  font-size: 14px;
}

.trait-level {
  color: rgba(255, 255, 255, 0.6);
  font-size: 12px;
}

.trait-effects {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.trait-effect {
  color: rgba(255, 255, 255, 0.7);
  font-size: 12px;
  line-height: 1.45;
}

.hero-source {
  padding: 10px 14px 14px;
  color: rgba(255, 255, 255, 0.55);
  font-size: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.hero-source a {
  color: rgba(233, 69, 96, 0.9);
  text-decoration: none;
}

.hero-source a:hover {
  text-decoration: underline;
}

.hero-empty {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: rgba(255, 255, 255, 0.7);
}

.hero-empty-title {
  font-size: 16px;
  font-weight: 700;
  color: #fff;
}

.hero-empty-tip {
  margin-top: 8px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
}
</style>

