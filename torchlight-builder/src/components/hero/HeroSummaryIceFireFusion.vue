<template>
  <div>
    <div class="hero-summary-title">冰火暴走伤害参考（冰焰 吉玛｜冰火融合）</div>
    <div v-if="canCalc && afterglowSelected" class="hero-summary-line">
      满配冰火暴走瞬时爆发（冰火融合 1 级，冰火相拥 5 级，冰火辉映 5 级）：
      <span class="hero-summary-highlight">
        火焰与冰冷伤害约 {{ fusionFullBurst.toFixed(1) }}%（约 {{ (1 + fusionFullBurst / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else-if="canCalc" class="hero-summary-line">
      仅冰火融合 + 冰火相拥参考（不计冰火辉映窗口）：
      <span class="hero-summary-highlight">
        火焰与冰冷伤害约 {{ fusionNoAfterglowBurst.toFixed(1) }}%（约 {{ (1 + fusionNoAfterglowBurst / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：冰火融合、冰火相拥；需要冰火辉映窗口效果请继续勾选“冰火辉映”。
    </div>

    <div class="hero-summary-form">
      <label v-if="embraceSelected" class="summary-field">
        <span>最近造成过火焰伤害</span>
        <select v-model="fusionHasRecentFire">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label v-if="embraceSelected" class="summary-field">
        <span>最近造成过冰冷伤害</span>
        <select v-model="fusionHasRecentCold">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label v-if="embraceSelected" class="summary-field">
        <span>冰火相拥等级</span>
        <select v-model.number="fusionEmbraceLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="afterglowSelected" class="summary-field">
        <span>当前处于冰火暴走结束后 3 秒窗口</span>
        <select v-model="fusionInAfterglow">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前单次冰火暴走爆发：
        <span class="hero-summary-highlight">
          火焰与冰冷伤害约 {{ fusionCurrentBurst.toFixed(1) }}%（约 {{ (1 + fusionCurrentBurst / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含冰火暴走本体 +20% 元素伤害、冰火相拥 的最近冰/火加成；冰火辉映在暴走结束后窗口内才会提供额外元素伤害；未计入元素穿透与抗性转换）
        </span>
      </template>
      <div v-else class="hero-summary-note" style="display: block;">
        需要勾选上述两项后再计算。
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

// 冰焰 吉玛｜冰火融合 冰火暴走爆发
const FUSION_EMBRACE_VALUES = [10, 13, 16, 19, 22] // 冰火相拥：最近火/冰对应的伤害%
const FUSION_AFTERGLOW = 100 // 冰火辉映：暴走结束后 3 秒窗口 +100% 火焰与冰冷伤害（按 5 级估算）

const fusionHasRecentFire = ref<boolean>(true)
const fusionHasRecentCold = ref<boolean>(true)
const fusionEmbraceLevel = ref<number>(5)
const fusionInAfterglow = ref<boolean>(true)

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('冰火融合'))
const embraceSelected = computed(() => selectedSet.value.has('冰火相拥'))
const afterglowSelected = computed(() => selectedSet.value.has('冰火辉映'))
const canCalc = computed(() => coreSelected.value && embraceSelected.value)

function calcFusionBurst(
  hasFire: boolean,
  hasCold: boolean,
  embraceLv: number,
  inAfterglow: boolean,
  hasCore: boolean,
  hasEmbrace: boolean,
  hasAfterglow: boolean
): number {
  const core = hasCore ? 20 : 0 // 冰火暴走本体：+20% 火焰与冰冷伤害
  const embracePer =
    hasEmbrace ? FUSION_EMBRACE_VALUES[Math.min(Math.max(embraceLv, 1), 5) - 1] || 0 : 0
  const fromFire = hasCold ? embracePer : 0
  const fromCold = hasFire ? embracePer : 0
  const embrace = fromFire + fromCold
  const afterglow = hasAfterglow && inAfterglow ? FUSION_AFTERGLOW : 0
  return core + embrace + afterglow
}

const fusionNoAfterglowBurst = computed(() => {
  if (!canCalc.value) return 0
  return calcFusionBurst(true, true, 5, false, true, true, false)
})

const fusionFullBurst = computed(() => {
  if (!canCalc.value || !afterglowSelected.value) return 0
  return calcFusionBurst(true, true, 5, true, true, true, true)
})

const fusionCurrentBurst = computed(() => {
  if (!canCalc.value) return 0
  return calcFusionBurst(
    fusionHasRecentFire.value,
    fusionHasRecentCold.value,
    fusionEmbraceLevel.value || 1,
    fusionInAfterglow.value,
    coreSelected.value,
    embraceSelected.value,
    afterglowSelected.value
  )
})
</script>

