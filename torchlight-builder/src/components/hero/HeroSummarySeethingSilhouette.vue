<template>
  <div>
    <div class="hero-summary-title">自身伤害增伤参考（狂人 雷恩｜怒影）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（已损生命 50%，盛怒之下 5 级，歇斯底里 5 级，斗气化形 5 级且层数最大）：
      <span class="hero-summary-highlight">
        约 {{ seethingFullBonus.toFixed(1) }}% 自身伤害（约 {{ (1 + seethingFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：盛怒之下、歇斯底里、斗气化形。
    </div>

    <div class="hero-summary-form">
      <label class="summary-field">
        <span>已损生命 %</span>
        <input v-model.number="lostLifePct" type="number" min="0" max="90" />
      </label>
      <label v-if="shengnuSelected" class="summary-field">
        <span>盛怒之下等级</span>
        <select v-model.number="shengnuLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="xiesiSelected" class="summary-field">
        <span>歇斯底里等级</span>
        <select v-model.number="xiesiLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="douqiSelected" class="summary-field">
        <span>斗气化形等级</span>
        <select v-model.number="douqiLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="douqiSelected" class="summary-field">
        <span>斗气层数</span>
        <input v-model.number="douqiStacks" type="number" min="0" max="10" />
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ seethingCurrentBonus.toFixed(1) }}% 自身伤害（约 {{ (1 + seethingCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含怒影核心 +20% 伤害、盛怒之下 自身伤害、歇斯底里 攻击伤害、斗气化形 层数伤害，不计召唤物与攻速频率）
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
const coreSelected = computed(() => selectedSet.value.has('怒影'))
const shengnuSelected = computed(() => selectedSet.value.has('盛怒之下'))
const xiesiSelected = computed(() => selectedSet.value.has('歇斯底里'))
const douqiSelected = computed(() => selectedSet.value.has('斗气化形'))
const canCalc = computed(() => coreSelected.value || shengnuSelected.value || xiesiSelected.value || douqiSelected.value)

// 狂人 雷恩｜怒影 自身伤害增伤计算
const SHENGNU_VALUES = [20, 27, 34, 41, 48] // 盛怒之下 自身伤害（%）
const XIESI_PER_LOST = [0.3, 0.4, 0.5, 0.6, 0.7] // 歇斯底里 每 1% 已损生命攻击伤害
const DOUQI_MAX_STACKS = [6, 7, 8, 9, 10] // 斗气化形 最大层数

const lostLifePct = ref<number>(50) // 已损生命百分比
const shengnuLevel = ref<number>(3)
const xiesiLevel = ref<number>(3)
const douqiLevel = ref<number>(3)
const douqiStacks = ref<number>(10)

function calcSeethingBonus(
  lostPct: number,
  shengnuLv: number,
  xiesiLv: number,
  douqiLv: number,
  stacks: number,
  hasCore: boolean,
  hasShengnu: boolean,
  hasXiesi: boolean,
  hasDouqi: boolean
): number {
  const baseFromCore = hasCore ? 20 : 0 // 怒影核心：暴气状态下，额外 +20% 伤害
  const shengnu = hasShengnu ? SHENGNU_VALUES[Math.min(Math.max(shengnuLv, 1), 5) - 1] || 0 : 0
  const perLost = hasXiesi ? XIESI_PER_LOST[Math.min(Math.max(xiesiLv, 1), 5) - 1] || 0 : 0
  const lost = hasXiesi ? Math.max(0, lostPct) * perLost : 0
  const maxStacks = hasDouqi ? DOUQI_MAX_STACKS[Math.min(Math.max(douqiLv, 1), 5) - 1] || 0 : 0
  const s = hasDouqi ? Math.min(Math.max(stacks, 0), maxStacks) : 0
  const douqi = hasDouqi ? s * 5 : 0 // 每层 +5% 伤害
  return baseFromCore + shengnu + lost + douqi
}

const seethingFullBonus = computed(() =>
  shengnuSelected.value && xiesiSelected.value && douqiSelected.value && coreSelected.value
    ? calcSeethingBonus(
        50,
        5,
        5,
        5,
        DOUQI_MAX_STACKS[4] /* 5级最大层数 10 */,
        true,
        true,
        true,
        true
      )
    : 0
)
const seethingCurrentBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcSeethingBonus(
    Math.max(0, lostLifePct.value || 0),
    shengnuLevel.value || 1,
    xiesiLevel.value || 1,
    douqiLevel.value || 1,
    douqiStacks.value || 0,
    coreSelected.value,
    shengnuSelected.value,
    xiesiSelected.value,
    douqiSelected.value
  )
})
</script>

