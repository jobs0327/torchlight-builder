<template>
  <div>
    <div class="hero-summary-title">麻痹与伤害参考（猫眼 艾瑞卡｜电光猫影）</div>
    <div v-if="canCalc" class="hero-summary-line">
      当前总麻痹效果提升：
      <span class="hero-summary-highlight">
        约 {{ lightningTotalParalysis.toFixed(1) }}% 麻痹效果
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：电光猫影、电镀狸纹、野性电光、猫驰电掣。
    </div>

    <div class="hero-summary-form">
      <label class="summary-field">
        <span>总移动速度%</span>
        <input v-model.number="lsMoveSpeedPct" type="number" min="0" max="300" />
      </label>
      <label v-if="coatSelected" class="summary-field">
        <span>电镀狸纹等级</span>
        <select v-model.number="lsCoatLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="wildSelected" class="summary-field">
        <span>野性电光等级</span>
        <select v-model.number="lsWildLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="rushSelected" class="summary-field">
        <span>猫驰电掣等级</span>
        <select v-model.number="lsRushLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="rushSelected" class="summary-field">
        <span>对目标累计麻痹层数</span>
        <input v-model.number="lsShockLayersApplied" type="number" min="0" max="40" />
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalc">
        猫驰电掣直接额外伤害：
        <span class="hero-summary-highlight">
          约 {{ lightningShockBonus.toFixed(1) }}% 伤害（约 {{ (1 + lightningShockBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （总麻痹效果提升用于对比不同配置；具体麻痹对伤害的放大倍率以游戏实际公式为准）
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
const baseSelected = computed(() => selectedSet.value.has('电光猫影'))
const coatSelected = computed(() => selectedSet.value.has('电镀狸纹'))
const wildSelected = computed(() => selectedSet.value.has('野性电光'))
const rushSelected = computed(() => selectedSet.value.has('猫驰电掣'))
const canCalc = computed(() => baseSelected.value && coatSelected.value && wildSelected.value && rushSelected.value)

// 猫眼 艾瑞卡｜电光猫影 麻痹 & 伤害
const LS_COAT_VALUES = [20, 25, 30, 35, 40] // 电镀狸纹
const LS_WILD_MAX = [80, 90, 100, 110, 120] // 野性电光上限
const LS_RUSH_PER = [1, 1.5, 2, 2.5, 3] // 猫驰电掣 每段伤害

const lsMoveSpeedPct = ref<number>(100)
const lsCoatLevel = ref<number>(5)
const lsWildLevel = ref<number>(5)
const lsRushLevel = ref<number>(5)
const lsShockLayersApplied = ref<number>(40)

const lightningTotalParalysis = computed(() => {
  if (!canCalc.value) return 0
  const base = 18
  const coat = LS_COAT_VALUES[Math.min(Math.max(lsCoatLevel.value || 1, 1), 5) - 1] || 0
  const maxWild = LS_WILD_MAX[Math.min(Math.max(lsWildLevel.value || 1, 1), 5) - 1] || 0
  const wildRaw = 0.4 * Math.max(0, lsMoveSpeedPct.value || 0)
  const wild = Math.min(wildRaw, maxWild)
  return base + coat + wild
})

const lightningShockBonus = computed(() => {
  if (!canCalc.value) return 0
  const per = LS_RUSH_PER[Math.min(Math.max(lsRushLevel.value || 1, 1), 5) - 1] || 0
  const stacks = Math.min(10, Math.floor(Math.max(0, lsShockLayersApplied.value || 0) / 4))
  return stacks * per
})
</script>

