<template>
  <div>
    <div class="hero-summary-title">霰弹投射物伤害参考（圣枪 卡里诺｜至暗掠影）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（危险间距 5 级 + 已选的 75 级分支 5 级，本次技能消耗 8 枚弹药）：
      <span class="hero-summary-highlight">
        约 {{ lethalFullBonus.toFixed(1) }}% 该次霰弹技能伤害（约 {{ (1 + lethalFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：危险间距，并在 75 级分支选择恶意入膛或孤注一掷。
    </div>
    <div class="hero-summary-form">
      <label class="summary-field">
        <span>消耗弹药数</span>
        <input v-model.number="lethalAmmoCount" type="number" min="0" max="10" />
      </label>
      <label v-if="maliceSelected" class="summary-field">
        <span>恶意入膛等级</span>
        <select v-model.number="lethalMaliceLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="dangerSelected" class="summary-field">
        <span>危险间距等级</span>
        <select v-model.number="lethalDangerLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="allinSelected" class="summary-field">
        <span>孤注一掷等级</span>
        <select v-model.number="lethalAllinLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ lethalCurrentBonus.toFixed(1) }}% 该次霰弹技能伤害（约 {{ (1 + lethalCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含危险间距 投射物伤害、对应已选 75 级分支的伤害加成）
        </span>
      </template>
      <div v-else class="hero-summary-note">
        需要先勾选危险间距，并选择 75 级分支后再计算。
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
const dangerSelected = computed(() => selectedSet.value.has('危险间距'))
const maliceSelected = computed(() => selectedSet.value.has('恶意入膛'))
const allinSelected = computed(() => selectedSet.value.has('孤注一掷'))
// 75 级分支只能二选一，因此只要选择了其一即可计算
const canCalc = computed(() => dangerSelected.value && (maliceSelected.value || allinSelected.value))

// 圣枪 卡里诺｜至暗掠影 霰弹技能单次伤害
const LETHAL_MALICE_VALUES = [0.6, 1.0, 1.4, 1.8, 2.2] // 恶意入膛 每层%
const LETHAL_DANGER_VALUES = [10, 16, 22, 28, 34] // 危险间距 投射物技能伤害
const LETHAL_ALLIN_VALUES = [9, 10, 11, 12, 13] // 孤注一掷 每枚弹药伤害

const lethalAmmoCount = ref<number>(8)
const lethalMaliceLevel = ref<number>(5)
const lethalDangerLevel = ref<number>(5)
const lethalAllinLevel = ref<number>(5)

function calcLethalBonus(
  ammoCount: number,
  maliceLv: number,
  dangerLv: number,
  allinLv: number,
  hasMalice: boolean,
  hasDanger: boolean,
  hasAllin: boolean
): number {
  const stacksMalice = Math.min(Math.max(ammoCount || 0, 0), 10)
  const malicePer = hasMalice
    ? LETHAL_MALICE_VALUES[Math.min(Math.max(maliceLv, 1), 5) - 1] || 0
    : 0
  const danger = hasDanger
    ? LETHAL_DANGER_VALUES[Math.min(Math.max(dangerLv, 1), 5) - 1] || 0
    : 0
  const allinPer = hasAllin
    ? LETHAL_ALLIN_VALUES[Math.min(Math.max(allinLv, 1), 5) - 1] || 0
    : 0
  const allinStacks = Math.min(Math.max(ammoCount || 0, 0), 8)
  const bMalice = stacksMalice * malicePer
  const bAllin = allinStacks * allinPer
  return danger + bMalice + bAllin
}

const lethalFullBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcLethalBonus(
    8,
    5,
    5,
    5,
    maliceSelected.value,
    dangerSelected.value,
    allinSelected.value
  )
})

const lethalCurrentBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcLethalBonus(
    lethalAmmoCount.value || 0,
    lethalMaliceLevel.value || 1,
    lethalDangerLevel.value || 1,
    lethalAllinLevel.value || 1,
    maliceSelected.value,
    dangerSelected.value,
    allinSelected.value
  )
})
</script>

