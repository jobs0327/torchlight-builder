<template>
  <div>
    <div class="hero-summary-title">投射物伤害参考（圣枪 卡里诺｜荣光游侠）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（基础 +35% 投射物伤害；弹药专家 5 级；倾泻 5 级；有备无患 5 级；本次技能消耗 4 枚特殊弹药）：
      <span class="hero-summary-highlight">
        约 {{ rangerFullBonus.toFixed(1) }}% 该次投射物技能伤害（约 {{ (1 + rangerFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：弹药专家、倾泻、有备无患。
    </div>
    <div class="hero-summary-form">
      <label class="summary-field">
        <span>消耗特殊弹药数</span>
        <input v-model.number="rangerAmmoCount" type="number" min="0" max="10" />
      </label>
      <label v-if="expertSelected" class="summary-field">
        <span>弹药专家等级</span>
        <select v-model.number="rangerExpertLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="qingxieSelected" class="summary-field">
        <span>倾泻等级</span>
        <select v-model.number="rangerQingxieLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="preparedSelected" class="summary-field">
        <span>有备无患等级</span>
        <select v-model.number="rangerPreparedLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ rangerCurrentBonus.toFixed(1) }}% 该次投射物技能伤害（约 {{ (1 + rangerCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含荣光游侠核心消耗弹药 +35% 投射物伤害、弹药专家本次技能伤害、有备无患本次技能伤害、倾泻对每枚特殊弹药的伤害加成）
        </span>
      </template>
      <div v-else class="hero-summary-note">
        需要勾选上述三个分支后再计算。
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

const selectedSet = computed(() =>
  new Set((props.selectedTraits ?? []).map(s => (s ?? '').trim()).filter(Boolean))
)
const coreSelected = computed(() => selectedSet.value.has('荣光游侠'))
const expertSelected = computed(() => selectedSet.value.has('弹药专家'))
const qingxieSelected = computed(() => selectedSet.value.has('倾泻'))
const preparedSelected = computed(() => selectedSet.value.has('有备无患'))
const canCalc = computed(() => coreSelected.value || expertSelected.value || qingxieSelected.value || preparedSelected.value)

// 圣枪 卡里诺｜荣光游侠 投射物技能单次伤害计算
const RANGER_EXPERT_VALUES = [15, 23, 31, 39, 47] // 弹药专家：消耗特殊弹药时，该次技能伤害
const RANGER_QINGXIE_VALUES = [5, 8, 11, 14, 17] // 倾泻：每枚特殊弹药伤害
const RANGER_PREPARED_VALUES = [15, 20, 25, 30, 35] // 有备无患：该次技能伤害

const rangerAmmoCount = ref<number>(4)
const rangerExpertLevel = ref<number>(5)
const rangerQingxieLevel = ref<number>(5)
const rangerPreparedLevel = ref<number>(5)

function calcRangerBonus(
  ammoCount: number,
  expertLv: number,
  qxLv: number,
  preparedLv: number,
  hasCore: boolean,
  hasExpert: boolean,
  hasQingxie: boolean,
  hasPrepared: boolean
): number {
  const baseFromCore = hasCore ? 35 : 0 // 荣光游侠核心：消耗弹药时，额外 +35% 投射物伤害
  const expert = hasExpert ? RANGER_EXPERT_VALUES[Math.min(Math.max(expertLv, 1), 5) - 1] || 0 : 0
  const perAmmo = hasQingxie ? RANGER_QINGXIE_VALUES[Math.min(Math.max(qxLv, 1), 5) - 1] || 0 : 0
  const prepared = hasPrepared ? RANGER_PREPARED_VALUES[Math.min(Math.max(preparedLv, 1), 5) - 1] || 0 : 0
  const ammo = hasQingxie ? Math.max(0, ammoCount || 0) * perAmmo : 0
  return baseFromCore + expert + prepared + ammo
}

const rangerFullBonus = computed(() =>
  expertSelected.value && qingxieSelected.value && preparedSelected.value && coreSelected.value
    ? calcRangerBonus(4, 5, 5, 5, true, true, true, true)
    : 0
)
const rangerCurrentBonus = computed(() => {
  return calcRangerBonus(
    rangerAmmoCount.value || 0,
    rangerExpertLevel.value || 1,
    rangerQingxieLevel.value || 1,
    rangerPreparedLevel.value || 1,
    coreSelected.value,
    expertSelected.value,
    qingxieSelected.value,
    preparedSelected.value
  )
})
</script>

