<template>
  <div>
    <div class="hero-summary-title">单次爆发与持续输出参考（逃脱者 宾｜创想鬼才）</div>

    <div v-if="coreSelected">
      <div class="hero-summary-line">
        单次法术迸发爆发（奇思爆破 + 奇思讯号）满配参考（灵感狂潮 5 级，危机创造 5 级）：
        <span class="hero-summary-highlight">
          约 {{ cgBurstFullBonus.toFixed(1) }}% 法术击中伤害（约 {{ (1 + cgBurstFullBonus / 100).toFixed(2) }} 倍）
        </span>
      </div>
      <div class="hero-summary-form">
        <label v-if="inspireSelected" class="summary-field">
          <span>灵感狂潮等级</span>
          <select v-model.number="cgInspireLevel">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
        <label v-if="signalSelected" class="summary-field">
          <span>危机创造等级</span>
          <select v-model.number="cgSignalLevel">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
      </div>
      <div class="hero-summary-result">
        当前单次爆发：
        <span class="hero-summary-highlight">
          约 {{ cgBurstCurrentBonus.toFixed(1) }}% 法术击中伤害（约 {{ (1 + cgBurstCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （假设目标已被奇思讯号影响：灵感狂潮 提升法术迸发释放技能击中伤害，危机创造 提升目标承受法术伤害）
        </span>
      </div>

      <div class="hero-summary-line" style="margin-top: 8px;">
        持续输出辅助指标（法术迸发上限与妙想素回复）：
        <span class="hero-summary-highlight">
          等效法术迸发上限 {{ cgEffectiveBurstLimit }} 层，妙想素回复倍率约 {{ cgSustainRegenMulti.toFixed(1) }} 倍
        </span>
      </div>
      <div class="hero-summary-form">
        <label class="summary-field">
          <span>基础法术迸发上限</span>
          <input v-model.number="cgBaseBurstLimit" type="number" min="1" max="5" />
        </label>
        <div class="hero-summary-note" style="margin: 0 0 8px 0;">
          （多元耦合方程：{{ coupleSelected ? '已点' : '未点' }}；妙想熵增法则：{{ entropySelected ? '已点' : '未点' }}）
        </div>
        <label v-if="entropySelected" class="summary-field">
          <span>妙想熵增法则等级</span>
          <select v-model.number="cgEntropyLevel">
            <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
          </select>
        </label>
      </div>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：创想鬼才（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('创想鬼才'))
const inspireSelected = computed(() => selectedSet.value.has('灵感狂潮'))
const signalSelected = computed(() => selectedSet.value.has('危机创造'))
const entropySelected = computed(() => selectedSet.value.has('妙想熵增法则'))
const coupleSelected = computed(() => selectedSet.value.has('多元耦合方程'))

// 逃脱者 宾｜创想鬼才 单次爆发 & 持续指标
const CG_INSPIRE_HIT = [10, 15, 20, 25, 30] // 灵感狂潮：法术迸发释放的技能击中伤害
const CG_SIGNAL_VALUES = [60, 60, 75, 75, 90] // 危机创造：奇思讯号 承受法术伤害
const CG_ENTROPY_VALUES = [4, 6, 8, 10, 12] // 妙想熵增法则：每层迸发上限 妙想素回复%

const cgInspireLevel = ref<number>(5)
const cgSignalLevel = ref<number>(5)

function calcCgBurstBonus(inspireLv: number, signalLv: number): number {
  const inspire = CG_INSPIRE_HIT[Math.min(Math.max(inspireLv, 1), 5) - 1] || 0
  const signal = CG_SIGNAL_VALUES[Math.min(Math.max(signalLv, 1), 5) - 1] || 0
  return inspire + signal
}

const cgBurstFullBonus = computed(() =>
  coreSelected.value && inspireSelected.value && signalSelected.value ? calcCgBurstBonus(5, 5) : 0
)
const cgBurstCurrentBonus = computed(() => {
  if (!coreSelected.value || !inspireSelected.value || !signalSelected.value) return 0
  return calcCgBurstBonus(cgInspireLevel.value || 1, cgSignalLevel.value || 1)
})

const cgBaseBurstLimit = ref<number>(3)
const cgEntropyLevel = ref<number>(5)

const cgEffectiveBurstLimit = computed(() => {
  if (!coreSelected.value) return 0
  const base = Math.max(1, cgBaseBurstLimit.value || 1)
  const extraCore = 1 // 创想鬼才基础 +1
  const extraCouple = coupleSelected.value ? 1 : 0 // 多元耦合方程 额外 +1
  return base + extraCore + extraCouple
})

const cgSustainRegenMulti = computed(() => {
  if (!coreSelected.value || !entropySelected.value) return 1
  const per = CG_ENTROPY_VALUES[Math.min(Math.max(cgEntropyLevel.value || 1, 1), 5) - 1] || 0
  const limit = cgEffectiveBurstLimit.value
  const bonus = limit * per
  return 1 + bonus / 100
})
</script>

