<template>
  <div>
    <div class="hero-summary-title">攻击伤害参考（猫眼 艾瑞卡｜疾风追猎）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（总移速 +100%，游兴 5 级，猫眼视界 5 级，猫爪连弹 5 级）：
      <span class="hero-summary-highlight">
        约 {{ windFullBonus.toFixed(1) }}% 自身攻击伤害（约 {{ (1 + windFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：游兴、猫眼视界、猫爪连弹。
    </div>
    <div class="hero-summary-form">
      <label class="summary-field">
        <span>总移动速度%</span>
        <input v-model.number="windMoveSpeedPct" type="number" min="0" max="300" />
      </label>
      <label v-if="youxingSelected" class="summary-field">
        <span>游兴等级</span>
        <select v-model.number="windYouxingLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="sightSelected" class="summary-field">
        <span>猫眼视界等级</span>
        <select v-model.number="windSightLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="comboSelected" class="summary-field">
        <span>猫爪连弹等级</span>
        <select v-model.number="windComboLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ windCurrentBonus.toFixed(1) }}% 自身攻击伤害（约 {{ (1 + windCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含游兴 将移动速度折算为攻击伤害、猫眼视界 额外伤害、猫爪连弹 的伤害修正）
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

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const youxingSelected = computed(() => selectedSet.value.has('游兴'))
const sightSelected = computed(() => selectedSet.value.has('猫眼视界'))
const comboSelected = computed(() => selectedSet.value.has('猫爪连弹'))
const canCalc = computed(() => youxingSelected.value && sightSelected.value && comboSelected.value)

// 猫眼 艾瑞卡｜疾风追猎 自身攻击伤害
const WIND_YOUXING_RATE = [20, 24, 28, 32, 36]
const WIND_YOUXING_CAP = [30, 36, 42, 48, 54]
const WIND_SIGHT_VALUES = [-4, 2, 8, 14, 20]
const WIND_COMBO_VALUES = [-18, -12, -6, 0, 6]

const windMoveSpeedPct = ref<number>(100)
const windYouxingLevel = ref<number>(3)
const windSightLevel = ref<number>(3)
const windComboLevel = ref<number>(3)

function calcWindBonus(
  movePct: number,
  youxingLv: number,
  sightLv: number,
  comboLv: number
): number {
  const rate = WIND_YOUXING_RATE[Math.min(Math.max(youxingLv, 1), 5) - 1] || 0
  const cap = WIND_YOUXING_CAP[Math.min(Math.max(youxingLv, 1), 5) - 1] || 0
  const raw = Math.max(0, movePct || 0) * (rate / 100)
  const youxing = Math.min(raw, cap)
  const sight = WIND_SIGHT_VALUES[Math.min(Math.max(sightLv, 1), 5) - 1] || 0
  const combo = WIND_COMBO_VALUES[Math.min(Math.max(comboLv, 1), 5) - 1] || 0
  return youxing + sight + combo
}

const windFullBonus = computed(() => (canCalc.value ? calcWindBonus(100, 5, 5, 5) : 0))
const windCurrentBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcWindBonus(
    windMoveSpeedPct.value || 0,
    windYouxingLevel.value || 1,
    windSightLevel.value || 1,
    windComboLevel.value || 1
  )
})
</script>

