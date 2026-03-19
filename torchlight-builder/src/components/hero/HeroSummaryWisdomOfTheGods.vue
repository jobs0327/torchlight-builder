<template>
  <div>
    <div class="hero-summary-title">神赐爆发与祝福层数参考（神谕者 希雅｜众神之伟智）</div>

    <!-- A. 单次神赐爆发面板增伤 -->
    <div v-if="coreSelected" class="hero-summary-line">
      单次神赐满配爆发参考（消耗 8 层聚能祝福，轮回预言 5 级，希望预言 5 级，终局预言 5 级，命中 10 个敌人）：
      <span class="hero-summary-highlight">
        约 {{ wisdomFullBurst.toFixed(1) }}% 面板伤害（约 {{ (1 + wisdomFullBurst / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：众神之伟智（核心）。
    </div>

    <div class="hero-summary-form">
      <label v-if="coreSelected" class="summary-field">
        <span>本次消耗聚能祝福层数</span>
        <input v-model.number="wisdomQLayers" type="number" min="0" max="8" />
      </label>
      <label v-if="coreSelected" class="summary-field">
        <span>本次消耗坚韧祝福层数</span>
        <input v-model.number="wisdomRLayers" type="number" min="0" max="20" />
      </label>
      <label v-if="coreSelected" class="summary-field">
        <span>本次消耗灵动祝福层数</span>
        <input v-model.number="wisdomMLayers" type="number" min="0" max="20" />
      </label>
      <label v-if="endSelected" class="summary-field">
        <span>终局预言等级</span>
        <select v-model.number="wisdomEndLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="cycleSelected" class="summary-field">
        <span>轮回预言等级</span>
        <select v-model.number="wisdomCycleLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="hopeSelected" class="summary-field">
        <span>希望预言等级</span>
        <select v-model.number="wisdomHopeLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="endSelected && coreSelected" class="summary-field">
        <span>神赐命中敌人数</span>
        <input v-model.number="wisdomEnemyCount" type="number" min="0" max="10" />
      </label>
    </div>

    <div v-if="coreSelected" class="hero-summary-result">
      当前单次神赐爆发：
      <span class="hero-summary-highlight">
        约 {{ wisdomCurrentBurst.toFixed(1) }}% 面板伤害（约 {{ (1 + wisdomCurrentBurst / 100).toFixed(2) }} 倍）
      </span>
      <span class="hero-summary-note">
        （包含众神之伟智核心：聚能祝福消耗增伤；其余增伤只计算你已选中的分支）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      无需计算。
    </div>

    <!-- B. 双倍/四倍伤害期望（告别预言） -->
    <div v-if="farewellSelected" class="hero-summary-line" style="margin-top: 8px;">
      双倍/四倍伤害期望（告别预言）：
      <span class="hero-summary-highlight">
        约 {{ wisdomExpectedMulti.toFixed(2) }} 倍期望伤害（仅考虑本次神赐叠满后的双倍/四倍结构）
      </span>
    </div>

    <div v-if="farewellSelected" class="hero-summary-form">
      <label class="summary-field">
        <span>告别预言等级</span>
        <select v-model.number="wisdomFarewellLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 神谕者 希雅｜众神之伟智 神赐爆发与双倍/四倍期望
const WISDOM_END_VALUES = [3, 3.7, 4.4, 5.1, 6] // 终局预言：每个敌人伤害%
const WISDOM_CYCLE_VALUES = [20, 24, 28, 32, 36] // 轮回预言：满层聚能额外伤害%
const WISDOM_HOPE_VALUES = [2, 2.3, 2.6, 2.9, 3.2] // 希望预言：每层祝福伤害%
const WISDOM_FAREWELL_VALUES = [4, 4.5, 5, 5.5, 6] // 告别预言：每层聚能双倍伤害几率%

const wisdomQLayers = ref<number>(8)
const wisdomRLayers = ref<number>(6)
const wisdomMLayers = ref<number>(6)
const wisdomEndLevel = ref<number>(5)
const wisdomCycleLevel = ref<number>(5)
const wisdomHopeLevel = ref<number>(5)
const wisdomEnemyCount = ref<number>(10)
const wisdomFarewellLevel = ref<number>(5)

function calcWisdomBurst(
  qLayers: number,
  rLayers: number,
  mLayers: number,
  endLv: number,
  cycleLv: number,
  hopeLv: number,
  enemyCount: number,
  hasCore: boolean,
  hasEnd: boolean,
  hasCycle: boolean,
  hasHope: boolean
): number {
  const q = Math.max(0, Math.min(qLayers || 0, 8))
  const r = Math.max(0, rLayers || 0)
  const m = Math.max(0, mLayers || 0)
  const enemies = Math.max(0, Math.min(enemyCount || 0, 10))

  // 核心：每层聚能祝福 +6% 伤害（最多 8 层）
  const core = hasCore ? q * 6 : 0

  // 终局预言：每个敌人额外伤害
  const endPer = WISDOM_END_VALUES[Math.min(Math.max(endLv, 1), 5) - 1] || 0
  const endBonus = hasEnd ? enemies * endPer : 0

  // 轮回预言：消耗满层聚能时的额外伤害
  const cyclePer = WISDOM_CYCLE_VALUES[Math.min(Math.max(cycleLv, 1), 5) - 1] || 0
  const cycleBonus = hasCycle && q >= 8 ? cyclePer : 0

  // 希望预言：每消耗一层祝福（聚能+坚韧+灵动）
  const totalBless = Math.min(q + r + m, 20)
  const hopePer = WISDOM_HOPE_VALUES[Math.min(Math.max(hopeLv, 1), 5) - 1] || 0
  const hopeBonus = hasHope ? totalBless * hopePer : 0

  return core + endBonus + cycleBonus + hopeBonus
}

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('众神之伟智'))
const endSelected = computed(() => selectedSet.value.has('终局预言'))
const cycleSelected = computed(() => selectedSet.value.has('轮回预言'))
const hopeSelected = computed(() => selectedSet.value.has('希望预言'))
const farewellSelected = computed(() => selectedSet.value.has('告别预言'))

const wisdomFullBurst = computed(() =>
  coreSelected.value
    ? calcWisdomBurst(8, 6, 6, 5, 5, 5, 10, true, endSelected.value, cycleSelected.value, hopeSelected.value)
    : 0
)

const wisdomCurrentBurst = computed(() =>
  coreSelected.value
    ? calcWisdomBurst(
        wisdomQLayers.value || 0,
        wisdomRLayers.value || 0,
        wisdomMLayers.value || 0,
        wisdomEndLevel.value || 1,
        wisdomCycleLevel.value || 1,
        wisdomHopeLevel.value || 1,
        wisdomEnemyCount.value || 0,
        coreSelected.value,
        endSelected.value,
        cycleSelected.value,
        hopeSelected.value
      )
    : 0
)

const wisdomExpectedMulti = computed(() => {
  if (!coreSelected.value || !farewellSelected.value) return 1
  const q = Math.max(0, Math.min(wisdomQLayers.value || 0, 10))
  const per =
    WISDOM_FAREWELL_VALUES[Math.min(Math.max(wisdomFarewellLevel.value || 1, 1), 5) - 1] || 0
  // 理论双倍几率（可超过 100，用于计算四倍部分）
  let p2 = q * per
  let p4 = 0
  if (p2 > 100) {
    // 溢出部分按“每 1% 溢出双倍几率 → 1% 四倍几率”粗略估算
    p4 = p2 - 100
    p2 = 100
  }
  const p2n = Math.min(p2, 100) / 100
  const p4n = Math.min(p4, 100) / 100
  const p0 = Math.max(0, 1 - p2n - p4n)

  return p0 * 1 + p2n * 2 + p4n * 4
})
</script>

