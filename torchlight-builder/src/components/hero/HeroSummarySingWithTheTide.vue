<template>
  <div>
    <div class="hero-summary-title">海潮接触伤害与海潮上收益参考（汐语 赛琳娜｜与海潮同歌）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      接触海潮的基础伤害加成（由海潮效果决定）：
      <span class="hero-summary-highlight">约 +{{ seaContactDamageBonusPct.toFixed(1) }}%</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      海潮上的额外伤害（叠加）：
      <span class="hero-summary-highlight">
        水波上的咏叹调 +{{ waveDamageOnSeaPct.toFixed(1) }}% ，牧歌移动贡献 +{{ herdingMoveBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      总计额外伤害加成（近似，所有额外%直接相加）：
      <span class="hero-summary-highlight">约 +{{ totalExtraDamagePct.toFixed(1) }}%</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label class="summary-field">
        <span>当前状态：高歌/吟游</span>
        <select v-model="isHighSong">
          <option :value="true">高歌</option>
          <option :value="false">吟游</option>
        </select>
      </label>

      <label v-if="waveSelected" class="summary-field">
        <span>水波上的咏叹调等级</span>
        <select v-model.number="waveTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>

      <label v-if="herdingSelected" class="summary-field">
        <span>海潮的牧歌等级</span>
        <select v-model.number="herdingTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="herdingSelected" class="summary-field">
        <span>海潮上移动距离（米，最多按 15 米叠层）</span>
        <input v-model.number="moveDistanceOnSeaMeters" type="number" min="0" max="60" step="0.5" />
      </label>

      <label v-if="submergeSelected" class="summary-field">
        <span>沉没一切的船歌等级（高歌时海潮效果额外）</span>
        <select v-model.number="submergeTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="submergeSelected" class="summary-field">
        <span>沉没一切的船歌叠层次数（0-2）</span>
        <input v-model.number="submergeStacks" type="number" min="0" max="2" step="1" />
      </label>

      <label v-if="flowSelected" class="summary-field">
        <span>流向远方的汐语等级（吟游时海潮效果额外）</span>
        <select v-model.number="flowTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：与海潮同歌（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('与海潮同歌'))
const waveSelected = computed(() => selectedSet.value.has('水波上的咏叹调'))
const herdingSelected = computed(() => selectedSet.value.has('海潮的牧歌'))
const submergeSelected = computed(() => selectedSet.value.has('沉没一切的船歌'))
const flowSelected = computed(() => selectedSet.value.has('流向远方的汐语'))

// 与海潮同歌：接触海潮额外 +15% 伤害（持续 4 秒）
const SEA_CONTACT_BASE = 15

// 高歌状态下：额外 +50% 海潮效果
const HIGH_SONG_EFFECT_EXTRA = 0.5

// 沉没一切的船歌：高歌状态期间额外 (+25/+35/+45/+55/+65)% 海潮效果，最多叠加 2 次
const SUBMERGE_EFFECT_PER_STACK = [25, 35, 45, 55, 65]

// 流向远方的汐语（吟游状态）：额外 (+60/+70/+80/+90/+100)% 海潮效果
const FLOW_EFFECT = [60, 70, 80, 90, 100]

// 水波上的咏叹调：对海潮上的敌人额外 (+10/+13/+16/+19/+22)% 伤害
const WAVE_ON_SEA = [10, 13, 16, 19, 22]

// 海潮的牧歌：每在海潮上移动 1 米，额外 (+1/1.3/1.6/1.9/2.2)% 伤害，最多 15 层
const HERDING_PER_METER = [1, 1.3, 1.6, 1.9, 2.2]
const HERDING_CAP_METERS = 15

const isHighSong = ref<boolean>(true)

const waveTraitLevel = ref<number>(3)
const herdingTraitLevel = ref<number>(3)
const moveDistanceOnSeaMeters = ref<number>(8)

const submergeTraitLevel = ref<number>(3)
const submergeStacks = ref<number>(1)

const flowTraitLevel = ref<number>(3)

const seaEffectMultiplier = computed(() => {
  if (!coreSelected.value) return 0
  // 海潮效果 = 基础 * (1 + 高歌/特性加成)
  let extra = 0
  if (isHighSong.value) {
    extra += HIGH_SONG_EFFECT_EXTRA
    if (submergeSelected.value) {
      const lvIdx = Math.min(Math.max(submergeTraitLevel.value || 1, 1), 5) - 1
      const perPct = SUBMERGE_EFFECT_PER_STACK[lvIdx] || 0
      extra += (perPct / 100) * Math.min(Math.max(submergeStacks.value || 0, 0), 2)
    }
  } else {
    if (flowSelected.value) {
      const lvIdx = Math.min(Math.max(flowTraitLevel.value || 1, 1), 5) - 1
      const perPct = FLOW_EFFECT[lvIdx] || 0
      extra += perPct / 100
    }
  }
  return 1 + extra
})

const seaContactDamageBonusPct = computed(() => {
  return SEA_CONTACT_BASE * seaEffectMultiplier.value
})

const waveDamageOnSeaPct = computed(() => {
  if (!coreSelected.value || !waveSelected.value) return 0
  const lvIdx = Math.min(Math.max(waveTraitLevel.value || 1, 1), 5) - 1
  return WAVE_ON_SEA[lvIdx] || 0
})

const herdingMoveBonusPct = computed(() => {
  if (!coreSelected.value || !herdingSelected.value) return 0
  const lvIdx = Math.min(Math.max(herdingTraitLevel.value || 1, 1), 5) - 1
  const per = HERDING_PER_METER[lvIdx] || 0
  const meters = Math.min(Math.max(moveDistanceOnSeaMeters.value || 0, 0), HERDING_CAP_METERS)
  return meters * per
})

const totalExtraDamagePct = computed(() => {
  if (!coreSelected.value) return 0
  return seaContactDamageBonusPct.value + waveDamageOnSeaPct.value + herdingMoveBonusPct.value
})
</script>

