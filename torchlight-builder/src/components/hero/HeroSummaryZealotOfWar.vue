<template>
  <div>
    <div class="hero-summary-title">投射物伤害参考（圣枪 卡里诺｜战火狂徒）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（升温层数取满层；焚尽荣光 5 级；战火永燃 5 级；60 级分支已选且 5 级）：
      <span class="hero-summary-highlight">
        约 {{ zealotFullBonus.toFixed(1) }}% 投射物伤害（约 {{ (1 + zealotFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：焚尽荣光、战火永燃，并在 60 级分支选择止战之息或极端温差。
    </div>
    <div class="hero-summary-form">
      <label class="summary-field">
        <span>当前升温层数</span>
        <input v-model.number="zealotHeatStacks" type="number" min="0" max="60" />
      </label>
      <label v-if="burnSelected" class="summary-field">
        <span>焚尽荣光等级</span>
        <select v-model.number="zealotBurnLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="breathSelected" class="summary-field">
        <span>止战之息等级</span>
        <select v-model.number="zealotBreathLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="extremeSelected" class="summary-field">
        <span>极端温差等级</span>
        <select v-model.number="zealotExtremeLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="eternalSelected" class="summary-field">
        <span>战火永燃等级</span>
        <select v-model.number="zealotEternalLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ zealotCurrentBonus.toFixed(1) }}% 投射物伤害（约 {{ (1 + zealotCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含战火狂徒核心 +20% 伤害、焚尽荣光升温伤害、已选 60 级分支与战火永燃的额外伤害）
        </span>
      </template>
      <div v-else class="hero-summary-note">
        需要勾选上述分支后再计算。
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

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const burnSelected = computed(() => selectedSet.value.has('焚尽荣光'))
const breathSelected = computed(() => selectedSet.value.has('止战之息'))
const extremeSelected = computed(() => selectedSet.value.has('极端温差'))
const eternalSelected = computed(() => selectedSet.value.has('战火永燃'))
const canCalc = computed(
  () => burnSelected.value && eternalSelected.value && (breathSelected.value || extremeSelected.value)
)

// 圣枪 卡里诺｜战火狂徒 投射物伤害
const ZEALOT_BURN_PER_STACK = [1.6, 2.0, 2.3, 2.6, 3.0] // 每层升温
const ZEALOT_BREATH_VALUES = [0, 5, 10, 16, 21] // 止战之息 额外伤害
const ZEALOT_EXTREME_VALUES = [0, 5, 5, 10, 16] // 极端温差
const ZEALOT_ETERNAL_VALUES = [0, 5, 10, 16, 21] // 战火永燃

const zealotHeatStacks = ref<number>(40)
const zealotBurnLevel = ref<number>(3)
const zealotBreathLevel = ref<number>(3)
const zealotExtremeLevel = ref<number>(3)
const zealotEternalLevel = ref<number>(3)

function calcZealotBonus(
  heatStacks: number,
  burnLv: number,
  breathLv: number,
  extremeLv: number,
  eternalLv: number,
  hasBurn: boolean,
  hasBreath: boolean,
  hasExtreme: boolean,
  hasEternal: boolean
): number {
  const core = 20
  const burnPer = hasBurn ? ZEALOT_BURN_PER_STACK[Math.min(Math.max(burnLv, 1), 5) - 1] || 0 : 0
  const bHeat = Math.max(0, heatStacks || 0) * burnPer
  const bBreath = hasBreath ? ZEALOT_BREATH_VALUES[Math.min(Math.max(breathLv, 1), 5) - 1] || 0 : 0
  const bExtreme = hasExtreme ? ZEALOT_EXTREME_VALUES[Math.min(Math.max(extremeLv, 1), 5) - 1] || 0 : 0
  const bEternal = hasEternal ? ZEALOT_ETERNAL_VALUES[Math.min(Math.max(eternalLv, 1), 5) - 1] || 0 : 0
  return core + bHeat + bBreath + bExtreme + bEternal
}

const zealotFullBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcZealotBonus(40, 5, 5, 5, 5, true, breathSelected.value, extremeSelected.value, true)
})

const zealotCurrentBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcZealotBonus(
    zealotHeatStacks.value || 0,
    zealotBurnLevel.value || 1,
    zealotBreathLevel.value || 1,
    zealotExtremeLevel.value || 1,
    zealotEternalLevel.value || 1,
    burnSelected.value,
    breathSelected.value,
    extremeSelected.value,
    eternalSelected.value
  )
})
</script>

