<template>
  <div class="pactspirit-page">
    <div class="pactspirit-sidebar">
      <div class="pactspirit-sidebar-head">
        <h2>契灵</h2>
        <span class="pactspirit-count">{{ items.length }}</span>
      </div>
      <p class="pactspirit-tip">数据来自本地 <code>pactspirit.json</code>，运行 <code>npm run sync:pactspirit</code> 更新。</p>
      <div class="pactspirit-filters" role="tablist" aria-label="契灵类型筛选">
        <button
          v-for="tab in petKindTabsWithCount"
          :key="tab.id"
          type="button"
          class="pactspirit-filter-tab"
          role="tab"
          :class="{ active: petKindFilter === tab.id }"
          :aria-selected="petKindFilter === tab.id"
          @click="petKindFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      <template v-if="petKindFilter === 'drop'">
        <div
          class="pactspirit-filters pactspirit-filters-play"
          role="tablist"
          aria-label="掉落玩法筛选"
        >
          <button
            v-for="tab in dropPlayTabs"
            :key="tab.id"
            type="button"
            class="pactspirit-filter-tab"
            role="tab"
            :class="{ active: dropPlayFilter === tab.id }"
            :aria-selected="dropPlayFilter === tab.id"
            @click="dropPlayFilter = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>
        <p class="pactspirit-play-hint">玩法标签由词条关键词自动归类。</p>
      </template>
      <template v-else-if="petKindFilter === 'battle'">
        <div
          class="pactspirit-filters pactspirit-filters-battle"
          role="tablist"
          aria-label="战斗宠分类筛选"
        >
          <button
            v-for="tab in battleClassTabs"
            :key="tab.id"
            type="button"
            class="pactspirit-filter-tab"
            role="tab"
            :class="{ active: battleClassFilter === tab.id }"
            :aria-selected="battleClassFilter === tab.id"
            @click="battleClassFilter = tab.id"
          >
            {{ tab.label }}
          </button>
        </div>
        <p class="pactspirit-play-hint">战斗分类按类型首行首词识别。</p>
      </template>
      <div class="pactspirit-filters" role="tablist" aria-label="稀有度筛选">
        <button
          v-for="tab in rarityTabs"
          :key="tab.id"
          type="button"
          class="pactspirit-filter-tab"
          role="tab"
          :class="{ active: rarityFilter === tab.id }"
          :aria-selected="rarityFilter === tab.id"
          @click="rarityFilter = tab.id"
        >
          {{ tab.label }}
        </button>
      </div>
      <div class="pactspirit-search">
        <input
          v-model="query"
          type="search"
          class="pactspirit-search-input"
          placeholder="按名称或词条搜索…"
          autocomplete="off"
          spellcheck="false"
        />
      </div>
      <div class="pactspirit-list">
        <button
          v-for="it in filteredItems"
          :key="it.id"
          type="button"
          class="pactspirit-row"
          :class="{ active: it.id === activeId, selected: isSelected(it) }"
          @click="activeId = it.id; toggleSelect(it)"
        >
          <span class="pactspirit-row-icon-wrap">
            <img v-if="it.iconUrl" :src="it.iconUrl" class="pactspirit-row-icon" alt="" />
          </span>
          <span class="pactspirit-row-text">
            <span class="pactspirit-row-name">{{ it.name }}</span>
            <span class="pactspirit-row-sub">
              <span
                class="pactspirit-row-kind"
                :data-pet-kind="isDropPet(it) ? 'drop' : 'battle'"
              >{{ petKindLabel(it) }}</span>
              <span v-if="isDropPet(it)" class="pactspirit-row-play">{{ dropPlayLabel(it) }}</span>
              <span v-if="it.rarityLabel" class="pactspirit-row-rarity" :data-rarity="it.rarityLabel">{{
                it.rarityLabel
              }}</span>
            </span>
          </span>
          <span class="pactspirit-row-actions">
            <button
              type="button"
              class="pactspirit-row-detail-btn"
              @click.stop="openDetail(it.id)"
            >
              详情
            </button>
          </span>
        </button>
        <p v-if="filteredItems.length === 0" class="pactspirit-empty">无匹配契灵</p>
      </div>
    </div>

    <div class="pactspirit-detail">
      <div class="pactspirit-detail-placeholder">
        <div class="pactspirit-config-title-row">
          <h3>宠物选择配置</h3>
          <p v-if="selectLimitTip" class="pactspirit-config-warning">
            <span class="pactspirit-config-warning-icon" aria-hidden="true">⚠</span>
            {{ selectLimitTip }}
          </p>
        </div>
        <p class="pactspirit-config-tip">默认每类最多选择 3 个：战斗宠 3 个 + 掉落宠 3 个。</p>
        <div class="pactspirit-config-counts">
          <div class="pactspirit-config-count-card">
            <span class="pactspirit-config-count-label">战斗宠</span>
            <strong class="pactspirit-config-count-value">{{ selectedBattleItems.length }}/3</strong>
          </div>
          <div class="pactspirit-config-count-card">
            <span class="pactspirit-config-count-label">掉落宠</span>
            <strong class="pactspirit-config-count-value">{{ selectedDropItems.length }}/3</strong>
          </div>
        </div>
        <div class="pactspirit-config-section">
          <h4 class="pactspirit-config-section-title">已选战斗宠</h4>
          <p v-if="selectedBattleItems.length === 0" class="pactspirit-config-empty">未选择</p>
          <ul v-else class="pactspirit-config-list">
            <li v-for="it in selectedBattleItems" :key="it.id" class="pactspirit-config-item">
              <span class="pactspirit-config-item-icon-wrap">
                <img v-if="it.iconUrl" :src="it.iconUrl" class="pactspirit-config-item-icon" alt="" />
              </span>
              <span class="pactspirit-config-item-name">{{ it.name }}</span>
              <button
                type="button"
                class="pactspirit-config-item-remove"
                aria-label="取消选择"
                @click.stop="removeSelected(it)"
              >
                ×
              </button>
            </li>
          </ul>
        </div>
        <div class="pactspirit-config-section">
          <h4 class="pactspirit-config-section-title">已选掉落宠</h4>
          <p v-if="selectedDropItems.length === 0" class="pactspirit-config-empty">未选择</p>
          <ul v-else class="pactspirit-config-list">
            <li v-for="it in selectedDropItems" :key="it.id" class="pactspirit-config-item">
              <span class="pactspirit-config-item-icon-wrap">
                <img v-if="it.iconUrl" :src="it.iconUrl" class="pactspirit-config-item-icon" alt="" />
              </span>
              <span class="pactspirit-config-item-name">{{ it.name }}</span>
              <button
                type="button"
                class="pactspirit-config-item-remove"
                aria-label="取消选择"
                @click.stop="removeSelected(it)"
              >
                ×
              </button>
            </li>
          </ul>
        </div>
        <div class="pactspirit-config-summary-grid">
          <div class="pactspirit-config-summary-card">
            <div class="pactspirit-config-summary-head">
              <h4 class="pactspirit-config-section-title">战斗加成汇总</h4>
              <span class="pactspirit-config-summary-badge">{{ aggregatedBattleStats.length }}</span>
            </div>
            <p v-if="aggregatedBattleStats.length === 0" class="pactspirit-config-empty">暂无可计算词条</p>
            <ul v-else class="pactspirit-config-stats">
              <li v-for="s in aggregatedBattleStats" :key="`battle-${s.effectKey}|${s.unit}|${s.kind}`">
                <span class="pactspirit-config-stat-key">{{ formatAggregateKey(s) }}</span>
                <span class="pactspirit-config-stat-val">{{ formatAggregateStat(s.value * battleStatMultiplier, s.unit) }}</span>
              </li>
            </ul>
          </div>
          <div class="pactspirit-config-summary-card">
            <div class="pactspirit-config-summary-head">
              <h4 class="pactspirit-config-section-title">掉落加成汇总</h4>
              <span class="pactspirit-config-summary-badge">{{ aggregatedDropStats.length }}</span>
            </div>
            <p v-if="aggregatedDropStats.length === 0" class="pactspirit-config-empty">暂无可计算词条</p>
            <ul v-else class="pactspirit-config-stats">
              <li v-for="s in aggregatedDropStats" :key="`drop-${s.effectKey}|${s.unit}|${s.kind}`">
                <span class="pactspirit-config-stat-key">{{ formatAggregateKey(s) }}</span>
                <span class="pactspirit-config-stat-val">{{ formatAggregateStat(s.value, s.unit) }}</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
      <div v-if="detailActive" class="pactspirit-detail-modal" @click.self="closeDetail">
        <div class="pactspirit-modal-panel">
          <header class="pactspirit-modal-head">
            <button type="button" class="pactspirit-modal-close" @click="closeDetail" aria-label="关闭详情">×</button>
          </header>
          <div class="pactspirit-detail">
            <header class="pactspirit-detail-head">
              <div class="pactspirit-detail-icon-wrap">
                <img v-if="detailActive.iconUrl" :src="detailActive.iconUrl" class="pactspirit-detail-icon" alt="" />
              </div>
              <div class="pactspirit-detail-titles">
                <h1 class="pactspirit-detail-name">{{ detailActive.name }}</h1>
                <div class="pactspirit-detail-meta">
                  <span
                    class="pactspirit-badge pactspirit-badge-pet"
                    :data-pet-kind="isDropPet(detailActive) ? 'drop' : 'battle'"
                  >{{ petKindLabel(detailActive) }}</span>
                  <span v-if="isDropPet(detailActive)" class="pactspirit-badge pactspirit-badge-play">{{
                    dropPlayLabel(detailActive)
                  }}</span>
                  <span v-if="detailActive.rarityLabel" class="pactspirit-badge">{{ detailActive.rarityLabel }}</span>
                  <a
                    class="pactspirit-tlidb-link"
                    :href="tlidbDetailUrl(detailActive)"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    TLIDB 详情
                  </a>
                </div>
              </div>
            </header>
            <section v-if="detailActive.tagLines?.length" class="pactspirit-section">
              <h3 class="pactspirit-section-title">类型</h3>
              <ul class="pactspirit-tag-lines">
                <li v-for="(line, i) in detailActive.tagLines" :key="i">{{ line }}</li>
              </ul>
            </section>
            <section v-if="detailEffectEntries.length" class="pactspirit-section">
              <h3 class="pactspirit-section-title">词条（结构化）</h3>
              <ul class="pactspirit-effects pactspirit-effects-entries">
                <li v-for="(entry, i) in detailEffectEntries" :key="`${entry.effectKey ?? entry.name}-${i}`">
                  <span class="pactspirit-entry-name">{{ entry.baseName ?? entry.name }}{{ formatTier(entry.tier) }}</span>
                  <span class="pactspirit-entry-value">{{ entry.valueText }}</span>
                  <span v-if="entry.valueParts?.length" class="pactspirit-entry-parts">
                    [{{ entry.valueParts.map(formatValuePart).join(', ') }}]
                  </span>
                </li>
              </ul>
            </section>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import pactspiritJson from '@/data/pactspirit.json'

type PactspiritItem = {
  id: string
  name: string
  detailPath: string
  iconUrl: string
  rarityClass?: string
  rarityLabel?: string | null
  tagLines?: string[]
  effectLines?: string[]
  effectEntries?: PactspiritEffectEntry[]
  calcStats?: { effectKey: string; kind: 'inc' | 'more'; unit: string; value: number }[]
}

type PactspiritEffectEntry = {
  name: string
  baseName?: string
  tier?: number | null
  effectKey?: string
  valueText: string
  sourceText?: string
  operator?: string | null
  valueNum?: number | null
  valueUnit?: string | null
  valueParts?: { operator: string; valueNum: number; valueUnit: string }[]
}
type PactspiritEffectValuePart = { operator: string; valueNum: number; valueUnit: string }

type RarityFilterId = 'all' | '魔法' | '稀有' | '传奇'
type PetKindFilterId = 'all' | 'drop' | 'battle'
type BattleClassId = 'all' | '攻击' | '法术' | '持续' | '召唤' | '生存' | '冰冷' | '闪电' | '火焰' | '腐蚀'

/** 掉落宠玩法 id（与筛选标签对应）；非掉落宠为 null。 */
type DropPlayId =
  | 'mistville'
  | 'doodle'
  | 'memory_fluor'
  | 'dark_tide'
  | 'ember_fuel'
  | 'ash'
  | 'void_seal'
  | 'star_hunt'
  | 'divine_stone'
  | 'eternal_maze'
  | 'nightmare'
  | 'club_gear'
  | 'tarot'
  | 'compass'
  | 'raid_trade'
  | 'train_heist'
  | 'overrealm'
  | 'surgeon'
  | 'generic'
  | 'unknown'

type DropPlayFilterId = 'all' | DropPlayId

const payload = pactspiritJson as { items?: PactspiritItem[] }
const items = payload.items ?? []

const query = ref('')
const activeId = ref(items[0]?.id ?? '')
const detailId = ref('')
const selectedBattleIds = ref<string[]>([])
const selectedDropIds = ref<string[]>([])
const selectLimitTip = ref('')
const petKindFilter = ref<PetKindFilterId>('all')
const dropPlayFilter = ref<DropPlayFilterId>('all')
const battleClassFilter = ref<BattleClassId>('all')
const rarityFilter = ref<RarityFilterId>('all')

/** TLIDB 列表「类型」首行以「掉落」开头为掉落宠，其余（攻击、召唤、法术等）为战斗宠。 */
function isDropPet(it: PactspiritItem): boolean {
  const first = (it.tagLines?.[0] ?? '').trim()
  return first.startsWith('掉落')
}

function petKindLabel(it: PactspiritItem): string {
  return isDropPet(it) ? '掉落宠' : '战斗宠'
}

function battleClassId(it: PactspiritItem): Exclude<BattleClassId, 'all'> | null {
  if (isDropPet(it)) return null
  const first = (it.tagLines?.[0] ?? '').trim()
  const kind = first.split(/\s+/)[0] ?? ''
  if (kind === '攻击' || kind === '法术' || kind === '持续' || kind === '召唤' || kind === '生存') return kind
  if (kind === '冰冷' || kind === '闪电' || kind === '火焰' || kind === '腐蚀') return kind
  return null
}

/**
 * 掉落玩法：按词条/类型文案中的关键词归类，首条命中为准（顺序影响「愚者」等多条玩法叠加之契灵）。
 */
const DROP_PLAY_RULES: readonly { kw: string; id: DropPlayId; label: string }[] = [
  { kw: '雾都', id: 'mistville', label: '雾都怪谈' },
  { kw: '笔触效果', id: 'doodle', label: '雪原' },
  { kw: '作画阶段', id: 'doodle', label: '雪原' },
  { kw: '专属地块', id: 'doodle', label: '雪原' },
  { kw: '记忆荧光', id: 'memory_fluor', label: '记忆荧光' },
  { kw: '黑潮', id: 'dark_tide', label: '黑潮' },
  { kw: '初火燃料', id: 'ember_fuel', label: '初火燃料' },
  { kw: '灰烬', id: 'ash', label: '灰烬' },
  { kw: '封印秘语', id: 'void_seal', label: '黑帆' },
  { kw: '虚海之子', id: 'void_seal', label: '黑帆' },
  { kw: '猎星之证', id: 'star_hunt', label: '季前赛' },
  { kw: '灾星首领', id: 'star_hunt', label: '季前赛' },
  { kw: '神威辉石', id: 'divine_stone', label: '魔方' },
  { kw: '永恒残垣', id: 'eternal_maze', label: '永恒迷城' },
  { kw: '烛台玩法', id: 'eternal_maze', label: '永恒迷城' },
  { kw: '永恒迷城', id: 'eternal_maze', label: '永恒迷城' },
  { kw: '梦境泡影', id: 'nightmare', label: '逃离噩梦' },
  { kw: '噩梦根系', id: 'nightmare', label: '逃离噩梦' },
  { kw: '怪谈之匣', id: 'mistville', label: '雾都怪谈' },
  { kw: '俱乐部游戏', id: 'club_gear', label: '俱乐部' },
  { kw: '齿轮作战', id: 'club_gear', label: '俱乐部' },
  { kw: '齿轮奖券', id: 'club_gear', label: '俱乐部' },
  { kw: '塔罗秘径', id: 'tarot', label: '塔罗秘径' },
  { kw: '塔罗师', id: 'tarot', label: '塔罗秘径' },
  { kw: '宿命对局', id: 'tarot', label: '塔罗秘径' },
  { kw: '命运之匣', id: 'tarot', label: '塔罗秘径' },
  { kw: '多多补给', id: 'compass', label: '罗盘' },
  { kw: '罗盘', id: 'compass', label: '罗盘' },
  { kw: '劫掠', id: 'raid_trade', label: '大亨' },
  { kw: '贸易完成', id: 'raid_trade', label: '大亨' },
  { kw: '订单结算', id: 'raid_trade', label: '大亨' },
  { kw: '劫车行动', id: 'train_heist', label: '劫车' },
  { kw: '高塔中央金库', id: 'train_heist', label: '劫车' },
  { kw: '重新编码', id: 'train_heist', label: '劫车' },
  { kw: '叠界', id: 'overrealm', label: '叠界' },
  { kw: '解药罐', id: 'surgeon', label: '疯医手术室' },
  { kw: '疯医雪莱', id: 'surgeon', label: '疯医手术室' },
  { kw: '手术室', id: 'surgeon', label: '疯医手术室' }
]

const dropPlayTabs: { id: DropPlayFilterId; label: string }[] = [
  { id: 'all', label: '全部玩法' },
  { id: 'mistville', label: '雾都怪谈' },
  { id: 'doodle', label: '雪原' },
  { id: 'memory_fluor', label: '记忆荧光' },
  { id: 'dark_tide', label: '黑潮' },
  { id: 'ember_fuel', label: '初火燃料' },
  { id: 'ash', label: '灰烬' },
  { id: 'void_seal', label: '黑帆' },
  { id: 'star_hunt', label: '季前赛' },
  { id: 'divine_stone', label: '魔方' },
  { id: 'eternal_maze', label: '永恒迷城' },
  { id: 'nightmare', label: '逃离噩梦' },
  { id: 'club_gear', label: '俱乐部' },
  { id: 'tarot', label: '塔罗秘径' },
  { id: 'compass', label: '罗盘' },
  { id: 'raid_trade', label: '大亨' },
  { id: 'train_heist', label: '劫车' },
  { id: 'overrealm', label: '叠界' },
  { id: 'surgeon', label: '疯医手术室' },
  { id: 'generic', label: '通用加成' },
  { id: 'unknown', label: '未分类' }
]

const battleClassTabs: { id: BattleClassId; label: string }[] = [
  { id: 'all', label: '全部战斗分类' },
  { id: '攻击', label: '攻击' },
  { id: '法术', label: '法术' },
  { id: '持续', label: '持续' },
  { id: '召唤', label: '召唤' },
  { id: '生存', label: '生存' },
  { id: '冰冷', label: '冰冷' },
  { id: '闪电', label: '闪电' },
  { id: '火焰', label: '火焰' },
  { id: '腐蚀', label: '腐蚀' }
]

function dropPlayId(it: PactspiritItem): DropPlayId | null {
  if (!isDropPet(it)) return null
  /** 葫狸葫兔（俗称糊里糊涂）：无词条时仍归入季前赛（猎心）玩法 */
  if (it.id === 'Fluffhead_Hare') return 'star_hunt'
  /** 缚心蔷薇：与神威辉石线合并为「魔方」 */
  if (it.id === 'Heart-binding_Rose') return 'divine_stone'
  /** 哀怨线球-金箔：归类到黑帆（原虚海封印） */
  if (it.id === 'Plaintive_Ball_of_Thread_-_Gold_Leaf') return 'void_seal'
  /** 快乐小肥-翡翠：归类到黑帆 */
  if (it.id === 'Happy_Chonky_-_Emerald') return 'void_seal'
  /** 游戏现版本未实装：暖阳、霜寒归类到未分类 */
  if (it.id === 'Happy_Chonky_-_Sun' || it.id === 'Plaintive_Ball_of_Thread_-_Frost') return 'unknown'
  /** 小咕咕菇-见手青、小灯龙-幽光：归类到叠界 */
  if (
    it.id === 'Shro-Shroom_-_Lurid_Bolete' ||
    it.id === 'Lumidrake_-_Glow' ||
    it.id === 'Shro-Shroom_-_Boletus' ||
    it.id === 'Lumidrake_-_Fluorescence'
  ) return 'overrealm'
  const blob = [...(it.tagLines ?? []), ...(it.effectLines ?? [])].join('\n')
  for (const r of DROP_PLAY_RULES) {
    if (blob.includes(r.kw)) return r.id
  }
  const fx = it.effectLines ?? []
  if (fx.length === 0) return 'unknown'
  return 'generic'
}

function dropPlayLabel(it: PactspiritItem): string {
  const id = dropPlayId(it)
  if (!id) return ''
  if (id === 'generic') return '通用加成'
  if (id === 'unknown') return '未分类'
  const hit = DROP_PLAY_RULES.find(r => r.id === id)
  return hit?.label ?? id
}

const petKindTabs: { id: PetKindFilterId; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'battle', label: '战斗宠' },
  { id: 'drop', label: '掉落宠' }
]

const petKindCounts = computed((): Record<PetKindFilterId, number> => {
  let drop = 0
  for (const it of items) {
    if (isDropPet(it)) drop += 1
  }
  const all = items.length
  const battle = all - drop
  return { all, battle, drop }
})

const petKindTabsWithCount = computed(() =>
  petKindTabs.map(tab => ({
    ...tab,
    label: `${tab.label} (${petKindCounts.value[tab.id]})`
  }))
)

const rarityTabs: { id: RarityFilterId; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: '魔法', label: '魔法' },
  { id: '稀有', label: '稀有' },
  { id: '传奇', label: '传奇' }
]

function raritySortRank(label: string | null | undefined): number {
  if (label === '传奇') return 0
  if (label === '稀有') return 1
  if (label === '魔法') return 2
  return 3
}

const filteredItems = computed((): PactspiritItem[] => {
  const q = query.value.trim().toLowerCase()
  let list = items
  if (petKindFilter.value === 'drop') {
    list = list.filter(isDropPet)
  } else if (petKindFilter.value === 'battle') {
    list = list.filter(it => !isDropPet(it))
  }
  if (petKindFilter.value === 'drop' && dropPlayFilter.value !== 'all') {
    list = list.filter(it => isDropPet(it) && dropPlayId(it) === dropPlayFilter.value)
  }
  if (petKindFilter.value === 'battle' && battleClassFilter.value !== 'all') {
    list = list.filter(it => !isDropPet(it) && battleClassId(it) === battleClassFilter.value)
  }
  if (rarityFilter.value !== 'all') {
    list = list.filter(it => it.rarityLabel === rarityFilter.value)
  }
  if (q) {
    list = list.filter(it => {
      if (it.name.toLowerCase().includes(q)) return true
      const blob = [...(it.tagLines ?? []), ...(it.effectLines ?? [])].join(' ').toLowerCase()
      return blob.includes(q)
    })
  }
  return [...list].sort((a, b) => {
    const ra = raritySortRank(a.rarityLabel)
    const rb = raritySortRank(b.rarityLabel)
    if (ra !== rb) return ra - rb
    return a.name.localeCompare(b.name, 'zh-CN')
  })
})

const active = computed((): PactspiritItem | null => {
  const id = activeId.value
  if (!id) return null
  return items.find(x => x.id === id) ?? null
})

const detailActive = computed((): PactspiritItem | null => {
  const id = detailId.value
  if (!id) return null
  return items.find(x => x.id === id) ?? null
})

const detailEffectEntries = computed((): PactspiritEffectEntry[] => {
  const list = detailActive.value?.effectEntries
  if (!Array.isArray(list)) return []
  return list.filter(
    (x): x is PactspiritEffectEntry =>
      !!x && typeof x === 'object' && typeof x.name === 'string' && typeof x.valueText === 'string'
  )
})

function formatTier(tier: number | null | undefined): string {
  if (!tier || tier < 1) return ''
  return ` ${tier}`
}

function formatValuePart(part: { operator: string; valueNum: number; valueUnit: string }): string {
  const num = Number.isInteger(part.valueNum) ? String(part.valueNum) : String(part.valueNum)
  const op = part.operator && part.operator !== '=' ? part.operator : ''
  const unit = part.valueUnit === '%' ? '%' : ''
  return `${op}${num}${unit}`
}

function isSelected(it: PactspiritItem): boolean {
  return isDropPet(it) ? selectedDropIds.value.includes(it.id) : selectedBattleIds.value.includes(it.id)
}

function toggleSelect(it: PactspiritItem): void {
  if (isDropPet(it)) {
    const arr = selectedDropIds.value
    const idx = arr.indexOf(it.id)
    if (idx >= 0) {
      arr.splice(idx, 1)
      return
    }
    if (arr.length >= 3) {
      showSelectLimitTip('掉落宠')
      return
    }
    arr.push(it.id)
    return
  }
  const arr = selectedBattleIds.value
  const idx = arr.indexOf(it.id)
  if (idx >= 0) {
    arr.splice(idx, 1)
    return
  }
  if (arr.length >= 3) {
    showSelectLimitTip('战斗宠')
    return
  }
  arr.push(it.id)
}

function showSelectLimitTip(kind: '战斗宠' | '掉落宠'): void {
  selectLimitTip.value = `${kind}最多只能选择 3 个`
}

function removeSelected(it: PactspiritItem): void {
  if (isDropPet(it)) {
    const idx = selectedDropIds.value.indexOf(it.id)
    if (idx >= 0) selectedDropIds.value.splice(idx, 1)
    return
  }
  const idx = selectedBattleIds.value.indexOf(it.id)
  if (idx >= 0) selectedBattleIds.value.splice(idx, 1)
}

const selectedBattleItems = computed(() =>
  selectedBattleIds.value.map(id => items.find(x => x.id === id)).filter((x): x is PactspiritItem => !!x)
)

const selectedDropItems = computed(() =>
  selectedDropIds.value.map(id => items.find(x => x.id === id)).filter((x): x is PactspiritItem => !!x)
)

function effectPartsOfEntry(entry: PactspiritEffectEntry): PactspiritEffectValuePart[] {
  if (Array.isArray(entry.valueParts) && entry.valueParts.length > 0) return entry.valueParts
  if (typeof entry.valueNum === 'number') {
    return [{ operator: entry.operator ?? '=', valueNum: entry.valueNum, valueUnit: entry.valueUnit ?? 'flat' }]
  }
  return []
}

type AggregateKind = 'inc' | 'more'
type AggregateRow = { effectKey: string; unit: string; value: number; kind: AggregateKind }
type AggregateMode = 'battle' | 'drop'

const MORE_KEYWORDS = ['额外', 'more'] as const
const DAMAGE_KEYWORDS = ['伤害', '召唤物伤害', '攻击伤害', '法术伤害'] as const
const EXCLUDE_VALUE_KEYWORDS = ['几率', '概率', '层数', '上限', '冷却', '回复', '命中', '触发'] as const

function isDamageKey(effectKey: string): boolean {
  return DAMAGE_KEYWORDS.some(k => effectKey.includes(k))
}

function shouldExcludeByValueText(text: string): boolean {
  return EXCLUDE_VALUE_KEYWORDS.some(k => text.includes(k))
}

function isMoreEntry(entry: PactspiritEffectEntry): boolean {
  const blob = `${entry.name ?? ''} ${entry.baseName ?? ''} ${entry.effectKey ?? ''} ${entry.valueText ?? ''}`.toLowerCase()
  return MORE_KEYWORDS.some(k => blob.includes(k.toLowerCase()))
}

function formatAggregateKey(row: AggregateRow): string {
  return row.kind === 'more' ? `${row.effectKey}（额外）` : `${row.effectKey}（普通）`
}

function normalizeBattleEffectKey(rawKey: string): string | null {
  const k = rawKey.trim()
  const battleMap: Record<string, string> = {
    伤害: '总伤害',
    攻击伤害: '攻击伤害',
    攻击暴击值: '攻击暴击值',
    攻击速度: '攻击速度',
    施法速度: '施法速度',
    攻施速度: '攻施速度',
    移动速度: '移动速度',
    投射物速度: '投射物速度',
    双倍攻击: '双倍攻击',
    双倍法术: '双倍法术',
    诅咒效果: '诅咒效果',
    诅咒敌人削弱: '诅咒敌人削弱',
    召唤物攻击与施法速度: '召唤物攻击与施法速度',
    召唤物最大生命: '召唤物最大生命',
    法术伤害: '法术伤害',
    持续伤害: '持续伤害',
    异常伤害: '异常伤害',
    暴击伤害: '暴击伤害',
    瘫痪几率: '瘫痪几率',
    麻痹效果: '麻痹效果',
    全域伤害: '全域伤害',
    投射物伤害: '投射物伤害',
    元素伤害: '元素伤害',
    火焰伤害: '火焰伤害',
    冰冷伤害: '冰冷伤害',
    闪电伤害: '闪电伤害',
    腐蚀伤害: '腐蚀伤害',
    引导伤害: '引导伤害',
    仆从伤害: '召唤物伤害',
    召唤物伤害: '召唤物伤害'
  }
  if (battleMap[k]) return battleMap[k]
  if (k.includes('伤害') && !k.includes('减免')) return k
  if (
    k.includes('暴击值') ||
    k.includes('攻击速度') ||
    k.includes('施法速度') ||
    k.includes('攻施速度') ||
    k.includes('移动速度') ||
    k.includes('投射物速度') ||
    k.includes('双倍') ||
    k.includes('诅咒') ||
    k.includes('召唤物攻击与施法速度') ||
    k.includes('召唤物最大生命') ||
    k.includes('瘫痪几率') ||
    k.includes('麻痹效果') ||
    k.includes('全域伤害')
  ) return k
  return null
}

function normalizeDropEffectKey(entry: PactspiritEffectEntry): string | null {
  const text = String(entry.valueText || '')
  // 优先从 valueText 抽取具体掉落项（如 初火燃料/灰烬/神威辉石/罗盘）
  const m = text.match(/([\u4e00-\u9fa5A-Za-z0-9_ ]+?)\s*掉落数量/)
  if (m?.[1]) {
    const target = m[1].trim()
    if (target && target !== '额外') return `${target}掉落数量`
  }
  const k = String(entry.effectKey || '').trim()
  if (k === '掉落数量' || k === '收集强化') return '掉落数量'
  if (k.endsWith('掉落数量')) return k
  return null
}

function aggregateStatsForItems(chosen: PactspiritItem[], mode: AggregateMode) {
  const byCalcStats = new Map<string, AggregateRow>()
  let hasAnyCalcStats = false
  for (const it of chosen) {
    const cs = it.calcStats
    if (!Array.isArray(cs) || cs.length === 0) continue
    hasAnyCalcStats = true
    for (const row of cs) {
      const effectKey = String(row.effectKey || '').trim()
      const kind = row.kind === 'more' ? 'more' : 'inc'
      const unit = row.unit === '%' ? '%' : 'flat'
      const value = Number(row.value)
      if (!effectKey || !Number.isFinite(value) || unit !== '%') continue
      if (mode === 'battle') {
        if (!normalizeBattleEffectKey(effectKey)) continue
      } else {
        // 掉落汇总只展示“xxx掉落数量”口径
        if (!effectKey.includes('掉落数量')) continue
      }
      const key = `${effectKey}|${unit}|${kind}`
      const cur = byCalcStats.get(key) ?? { effectKey, unit, value: 0, kind }
      cur.value += value
      byCalcStats.set(key, cur)
    }
  }
  if (hasAnyCalcStats) {
    return [...byCalcStats.values()]
      .filter(x => Math.abs(x.value) > 0)
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  }

  const bucket = new Map<string, AggregateRow>()
  for (const it of chosen) {
    const entries = Array.isArray(it.effectEntries) ? it.effectEntries : []
    for (const e of entries) {
      const rawKey = String(e.effectKey || e.baseName || e.name || '').trim()
      if (!rawKey) continue
      let effectKey: string | null = null
      if (mode === 'battle') {
        effectKey = normalizeBattleEffectKey(rawKey)
        if (!effectKey) continue
        if (shouldExcludeByValueText(String(e.valueText || ''))) continue
      } else {
        effectKey = normalizeDropEffectKey(e)
        if (!effectKey) continue
      }
      const kind: AggregateKind = isMoreEntry(e) ? 'more' : 'inc'
      for (const p of effectPartsOfEntry(e)) {
        const sign = p.operator === '-' ? -1 : p.operator === '+' ? 1 : 0
        if (sign === 0) continue
        const unit = p.valueUnit === '%' ? '%' : 'flat'
        if (unit !== '%') continue
        const key = `${effectKey}|${unit}|${kind}`
        const cur = bucket.get(key) ?? { effectKey, unit, value: 0, kind }
        cur.value += sign * p.valueNum
        bucket.set(key, cur)
      }
    }
  }
  return [...bucket.values()]
    .filter(x => Math.abs(x.value) > 0)
    .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
}

const aggregatedBattleStats = computed(() => aggregateStatsForItems(selectedBattleItems.value, 'battle'))
const aggregatedDropStats = computed(() => aggregateStatsForItems(selectedDropItems.value, 'drop'))
const battleStatMultiplier = 1

function formatAggregateStat(value: number, unit: string): string {
  const sign = value > 0 ? '+' : ''
  const n = Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/\.00$/, '')
  return `${sign}${n}${unit === '%' ? '%' : ''}`
}

function openDetail(id: string): void {
  detailId.value = id
}

function closeDetail(): void {
  detailId.value = ''
}

function tlidbDetailUrl(it: PactspiritItem): string {
  const p = it.detailPath.startsWith('/') ? it.detailPath : `/${it.detailPath}`
  return `https://tlidb.com${p}`
}

watch(
  filteredItems,
  list => {
    if (!list.length) return
    if (!list.some(x => x.id === activeId.value)) {
      activeId.value = list[0]!.id
    }
  },
  { immediate: true }
)

watch(petKindFilter, v => {
  if (v === 'all') {
    dropPlayFilter.value = 'all'
    battleClassFilter.value = 'all'
  }
  if (v === 'battle') dropPlayFilter.value = 'all'
  if (v === 'drop') battleClassFilter.value = 'all'
})
</script>

<style scoped>
.pactspirit-page {
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

.pactspirit-sidebar {
  width: min(360px, 38vw);
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.pactspirit-sidebar-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
  margin-bottom: 8px;
}

.pactspirit-sidebar-head h2 {
  margin: 0;
  font-size: 20px;
}

.pactspirit-count {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.55);
}

.pactspirit-tip {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.55);
}

.pactspirit-tip code {
  font-size: 11px;
  color: rgba(180, 220, 255, 0.9);
}

.pactspirit-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.pactspirit-filters + .pactspirit-filters {
  margin-top: -2px;
}

.pactspirit-filter-tab {
  padding: 5px 11px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(0, 0, 0, 0.25);
  color: rgba(255, 255, 255, 0.78);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
}

.pactspirit-filter-tab:hover {
  border-color: rgba(233, 69, 96, 0.45);
  color: #fff;
}

.pactspirit-filter-tab.active {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.15);
  color: #fff;
}

.pactspirit-filters:last-of-type {
  margin-bottom: 10px;
}

.pactspirit-filters-play .pactspirit-filter-tab {
  font-size: 11px;
  padding: 4px 9px;
}

.pactspirit-play-hint {
  margin: -4px 0 8px;
  font-size: 11px;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.42);
}

.pactspirit-search {
  margin-bottom: 10px;
}

.pactspirit-search-input {
  width: 100%;
  box-sizing: border-box;
  padding: 9px 11px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  font-size: 13px;
}

.pactspirit-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
  scrollbar-width: thin;
  scrollbar-color: rgba(233, 69, 96, 0.8) rgba(255, 255, 255, 0.08);
}

.pactspirit-list::-webkit-scrollbar {
  width: 8px;
}

.pactspirit-list::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.08);
  border-radius: 999px;
}

.pactspirit-list::-webkit-scrollbar-thumb {
  background: rgba(233, 69, 96, 0.8);
  border-radius: 999px;
}

.pactspirit-list::-webkit-scrollbar-thumb:hover {
  background: rgba(233, 69, 96, 0.95);
}

.pactspirit-row {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding: 8px 10px;
  border: none;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  background: transparent;
  color: inherit;
  text-align: left;
  cursor: pointer;
}

.pactspirit-row:last-child {
  border-bottom: none;
}

.pactspirit-row:hover {
  background: rgba(233, 69, 96, 0.08);
}

.pactspirit-row.active {
  background: rgba(233, 69, 96, 0.16);
}

.pactspirit-row.selected {
  box-shadow: inset 0 0 0 1px rgba(166, 230, 162, 0.6);
  background: rgba(166, 230, 162, 0.12);
}

.pactspirit-row-icon-wrap {
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.4);
}

.pactspirit-row-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pactspirit-row-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.pactspirit-row-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pactspirit-row-sub {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
}

.pactspirit-row-kind {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.03em;
  padding: 2px 6px;
  border-radius: 4px;
  border: 1px solid transparent;
}

.pactspirit-row-kind[data-pet-kind='drop'] {
  color: #ffd89a;
  background: rgba(255, 170, 64, 0.14);
  border-color: rgba(255, 190, 100, 0.35);
}

.pactspirit-row-kind[data-pet-kind='battle'] {
  color: #b8e0ff;
  background: rgba(100, 180, 255, 0.12);
  border-color: rgba(120, 200, 255, 0.35);
}

.pactspirit-row-play {
  max-width: 100%;
  font-size: 10px;
  font-weight: 600;
  color: rgba(200, 220, 255, 0.72);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.pactspirit-row-rarity {
  font-size: 11px;
  color: rgba(255, 200, 160, 0.85);
}

.pactspirit-row-actions {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 6px;
}

.pactspirit-row-detail-btn {
  border: 1px solid rgba(126, 200, 255, 0.45);
  background: rgba(126, 200, 255, 0.14);
  color: #c4e9ff;
  border-radius: 6px;
  padding: 3px 8px;
  font-size: 11px;
  font-weight: 600;
  cursor: pointer;
}

.pactspirit-row-detail-btn:hover {
  background: rgba(126, 200, 255, 0.2);
}


.pactspirit-empty {
  margin: 14px;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.5);
}

.pactspirit-detail {
  flex: 1;
  min-width: 0;
  padding: 4px 8px;
  position: relative;
  display: flex;
}

.pactspirit-detail-placeholder {
  width: 100%;
  min-height: 100%;
  box-sizing: border-box;
  min-height: 240px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 18px;
  background: rgba(0, 0, 0, 0.22);
}

.pactspirit-detail-placeholder h3 {
  margin: 0;
}

.pactspirit-config-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 10px;
}

.pactspirit-detail-placeholder p {
  margin: 0;
  color: rgba(255, 255, 255, 0.7);
}

.pactspirit-config-tip {
  margin: 0 0 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.62);
}

.pactspirit-config-warning {
  margin: 0;
  font-size: 12px;
  color: #ffb5b5;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 92, 92, 0.55);
  background: rgba(120, 12, 12, 0.34);
}

.pactspirit-config-warning-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  border-radius: 999px;
  background: rgba(255, 82, 82, 0.25);
  color: #ff6b6b;
  font-size: 11px;
  line-height: 1;
}

.pactspirit-config-counts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 14px;
}

.pactspirit-config-count-card {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  padding: 8px 10px;
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 8px;
}

.pactspirit-config-count-label {
  font-size: 12px;
  color: rgba(210, 230, 255, 0.75);
}

.pactspirit-config-count-value {
  font-size: 14px;
  font-variant-numeric: tabular-nums;
}

.pactspirit-config-section {
  margin-top: 10px;
}

.pactspirit-config-section-title {
  margin: 0 0 6px;
  font-size: 13px;
  color: rgba(235, 244, 255, 0.92);
}

.pactspirit-config-empty {
  color: rgba(255, 255, 255, 0.45);
  font-size: 12px;
}

.pactspirit-config-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.pactspirit-config-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 4px 8px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
  min-width: 0;
  max-width: 100%;
}

.pactspirit-config-item-icon-wrap {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  border-radius: 999px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.35);
}

.pactspirit-config-item-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pactspirit-config-item-name {
  min-width: 0;
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 12px;
  line-height: 1.2;
  color: rgba(235, 244, 255, 0.9);
}

.pactspirit-config-item-remove {
  width: 18px;
  height: 18px;
  border-radius: 999px;
  border: none;
  background: rgba(255, 120, 120, 0.14);
  color: rgba(255, 210, 210, 0.95);
  font-size: 12px;
  line-height: 1;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  flex-shrink: 0;
}

.pactspirit-config-item-remove:hover {
  background: rgba(255, 120, 120, 0.25);
}

.pactspirit-config-summary-grid {
  margin-top: 12px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}

.pactspirit-config-summary-card {
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.03);
  border-radius: 10px;
  padding: 10px;
  min-height: 120px;
}

.pactspirit-config-summary-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 6px;
}

.pactspirit-config-summary-badge {
  min-width: 24px;
  text-align: center;
  font-size: 11px;
  font-weight: 700;
  padding: 2px 7px;
  border-radius: 999px;
  color: rgba(210, 230, 255, 0.9);
  background: rgba(126, 200, 255, 0.18);
  border: 1px solid rgba(126, 200, 255, 0.35);
}

.pactspirit-config-stats {
  margin: 0;
  padding: 0;
  list-style: none;
  display: grid;
  gap: 4px;
}

.pactspirit-config-stats li {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  font-size: 12px;
  border-bottom: 1px dashed rgba(255, 255, 255, 0.12);
  padding-bottom: 3px;
}

.pactspirit-config-stat-key {
  color: rgba(210, 230, 255, 0.9);
}

.pactspirit-config-stat-val {
  color: rgba(255, 255, 255, 0.9);
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1050px) {
  .pactspirit-config-summary-grid {
    grid-template-columns: 1fr;
  }
}

.pactspirit-detail-head {
  display: flex;
  gap: 16px;
  align-items: flex-start;
  margin-bottom: 20px;
}

.pactspirit-detail-icon-wrap {
  width: 72px;
  height: 72px;
  flex-shrink: 0;
  border-radius: 12px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.45);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.pactspirit-detail-icon {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.pactspirit-detail-name {
  margin: 0 0 8px;
  font-size: 22px;
  line-height: 1.25;
}

.pactspirit-detail-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.pactspirit-badge {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: rgba(233, 69, 96, 0.2);
  border: 1px solid rgba(233, 69, 96, 0.45);
  color: #ffb4c0;
}

.pactspirit-badge-pet[data-pet-kind='drop'] {
  background: rgba(255, 170, 64, 0.16);
  border-color: rgba(255, 190, 100, 0.5);
  color: #ffd89a;
}

.pactspirit-badge-pet[data-pet-kind='battle'] {
  background: rgba(100, 180, 255, 0.14);
  border-color: rgba(120, 200, 255, 0.45);
  color: #b8e0ff;
}

.pactspirit-badge-play {
  background: rgba(160, 140, 255, 0.14);
  border-color: rgba(180, 160, 255, 0.42);
  color: #d4c8ff;
}

.pactspirit-tlidb-link {
  font-size: 13px;
  color: #7ec8ff;
  text-decoration: none;
}

.pactspirit-tlidb-link:hover {
  text-decoration: underline;
}

.pactspirit-section {
  margin-bottom: 18px;
}

.pactspirit-section-title {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.75);
}

.pactspirit-tag-lines,
.pactspirit-effects {
  margin: 0;
  padding-left: 1.1rem;
  font-size: 14px;
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.88);
}

.pactspirit-effects li {
  margin-bottom: 6px;
}

.pactspirit-effects-entries {
  list-style: none;
  padding-left: 0;
}

.pactspirit-effects-entries li {
  display: grid;
  grid-template-columns: minmax(120px, 180px) 1fr;
  gap: 6px 10px;
  align-items: baseline;
  padding: 6px 8px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.02);
}

.pactspirit-entry-name {
  font-size: 13px;
  font-weight: 600;
  color: rgba(190, 225, 255, 0.95);
}

.pactspirit-entry-value {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.9);
}

.pactspirit-entry-parts {
  grid-column: 1 / -1;
  font-size: 11px;
  color: rgba(180, 200, 230, 0.75);
}

.pactspirit-detail-modal {
  position: absolute;
  inset: 0;
  z-index: 20;
  background: rgba(0, 0, 0, 0.62);
  display: flex;
  justify-content: stretch;
  align-items: stretch;
  border-radius: 12px;
}

.pactspirit-modal-panel {
  width: 100%;
  max-height: 100%;
  overflow: auto;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.15);
  background: #12131b;
  box-shadow: 0 10px 36px rgba(0, 0, 0, 0.42);
}

.pactspirit-modal-head {
  position: sticky;
  top: 0;
  z-index: 1;
  display: flex;
  justify-content: flex-end;
  padding: 10px 12px;
  background: rgba(18, 19, 27, 0.94);
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.pactspirit-modal-close {
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.92);
  border-radius: 0;
  padding: 2px 6px;
  font-size: 20px;
  line-height: 1;
  font-weight: 500;
  cursor: pointer;
}

.pactspirit-detail-empty {
  padding: 48px 16px;
  text-align: center;
  color: rgba(255, 255, 255, 0.45);
  font-size: 15px;
}
</style>
