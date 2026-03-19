<template>
  <div>
    <div class="hero-summary-title">持续伤害与时空乱流参考（时空见证者 尤加｜时空流逝）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      扭曲时空记录的所有伤害（期望倍率）：
      <span class="hero-summary-highlight">
        ×{{ recordedAllDamageMultiplier.toFixed(2) }}
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      总增伤参考（连续伤害额外 + 记录分摊）：约 +{{ totalBonusDamagePct.toFixed(1) }}%
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="accelSelected" class="summary-field">
        <span>时空加速等级（每秒加成）</span>
        <select v-model.number="accelTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field">
        <span>扭曲时空有效存在秒数</span>
        <input v-model.number="baseDistortionSeconds" type="number" min="0" max="20" step="0.5" />
      </label>
      <label v-if="changeSelected" class="summary-field">
        <span>时空剧变等级（连续伤害额外）</span>
        <select v-model.number="changeTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="stopSelected" class="summary-field">
        <span>时空停滞等级（记录伤害额外）</span>
        <select v-model.number="stopTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="inflateSelected" class="summary-field">
        <span>时空膨胀等级（持续时间额外）</span>
        <select v-model.number="inflateTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：时空流逝（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('时空流逝'))
const accelSelected = computed(() => selectedSet.value.has('时空加速'))
const changeSelected = computed(() => selectedSet.value.has('时空剧变'))
const stopSelected = computed(() => selectedSet.value.has('时空停滞'))
const inflateSelected = computed(() => selectedSet.value.has('时空膨胀'))

// 核心：时空流逝记录 30% 持续/收割/净化切割伤害
const CORE_RECORD_SHARE = 30 // %

// 时空加速：扭曲时空每存在 1 秒，(+5/6.5/8/9.5/11)% 记录的所有伤害，最多叠加 5 层
const ACCEL_PER_LEVEL = [5, 6.5, 8, 9.5, 11]
const ACCEL_MAX_STACKS = 5

// 时空剧变：额外 (+30/37/44/51/58)% 持续伤害
const CHANGE_PER_LEVEL = [30, 37, 44, 51, 58]

// 时空停滞： (+60/+70/+80/+90/+100)% 扭曲时空记录的所有伤害
const STOP_RECORDED_PER_LEVEL = [60, 70, 80, 90, 100]

// 时空膨胀：额外 (+50/+62/+74/+86/+98)% 扭曲时空与时空乱流持续时间
const INFLATE_DURATION_PER_LEVEL = [50, 62, 74, 86, 98]

const accelTraitLevel = ref<number>(5)
const changeTraitLevel = ref<number>(5)
const stopTraitLevel = ref<number>(5)
const inflateTraitLevel = ref<number>(5)

const baseDistortionSeconds = ref<number>(6) // 与核心描述一致：持续 6 秒（此处用于计算膨胀后存在时长）

const inflatedSeconds = computed(() => {
  const lvIdx = Math.min(Math.max(inflateTraitLevel.value || 1, 1), 5) - 1
  const addPct = inflateSelected.value ? INFLATE_DURATION_PER_LEVEL[lvIdx] || 0 : 0
  return Math.max(0, baseDistortionSeconds.value || 0) * (1 + addPct / 100)
})

const accelStacks = computed(() => {
  if (!accelSelected.value) return 0
  return Math.min(ACCEL_MAX_STACKS, Math.floor(Math.max(0, inflatedSeconds.value) || 0))
})

const recordedAllDamageMultiplier = computed(() => {
  const accelLvIdx = Math.min(Math.max(accelTraitLevel.value || 1, 1), 5) - 1
  const perAccel = ACCEL_PER_LEVEL[accelLvIdx] || 0
  const accelBonusPct = accelSelected.value ? accelStacks.value * perAccel : 0

  const stopLvIdx = Math.min(Math.max(stopTraitLevel.value || 1, 1), 5) - 1
  const stopBonusPct = STOP_RECORDED_PER_LEVEL[stopLvIdx] || 0

  // 记录伤害倍率：1 + accelBonus + stopBonus（近似按加和处理）
  return 1 + (accelBonusPct + (stopSelected.value ? stopBonusPct : 0)) / 100
})

const recordedSplitBonusDamagePct = computed(() => {
  // 记录共享：30% * 记录伤害倍率
  return (CORE_RECORD_SHARE * recordedAllDamageMultiplier.value) / 1
})

const continuousExtraDamagePct = computed(() => {
  if (!changeSelected.value) return 0
  const lvIdx = Math.min(Math.max(changeTraitLevel.value || 1, 1), 5) - 1
  return CHANGE_PER_LEVEL[lvIdx] || 0
})

const totalBonusDamagePct = computed(() => {
  return continuousExtraDamagePct.value + recordedSplitBonusDamagePct.value
})
</script>

