<template>
  <div>
    <div class="hero-summary-title">暖风层数与神灵伤害参考（遗世魔灵 伊瑞斯｜守望的暖风）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      估算暖风层数上限（由“最温暖的守望”影响）：
      <span class="hero-summary-highlight">{{ computedWarmMax }} 层</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      估算当前暖风层数（在守望状态内的非重聚/重聚阶段 + 可选大招叠层）：
      <span class="hero-summary-highlight">{{ currentWarmStacks }} 层</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      额外伤害（“最喜悦的重逢”：守望状态期间每个魔灵 +{{ joyPerPct.toFixed(1) }}% 伤害）：
      <span class="hero-summary-highlight">{{ extraDamagePct.toFixed(1) }}%</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label class="summary-field">
        <span>守望状态起始暖风层数</span>
        <input v-model.number="startWarmStacks" type="number" min="0" max="30" step="1" />
      </label>
      <label class="summary-field">
        <span>非重聚阶段时长（秒）</span>
        <input v-model.number="nonRegroupSeconds" type="number" min="0" max="60" step="1" />
      </label>
      <label class="summary-field">
        <span>重聚阶段时长（秒）</span>
        <input v-model.number="regroupSeconds" type="number" min="0" max="60" step="1" />
      </label>

      <label class="summary-field">
        <span v-if="sameRivalSelected">同烈风共舞等级（大招触发层数）</span>
        <span v-else>（同烈风共舞未选择）</span>
        <select v-model.number="sameRivalLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="sameRivalSelected" class="summary-field">
        <span>释放大招次数</span>
        <input v-model.number="ultimateCount" type="number" min="0" max="50" step="1" />
      </label>

      <label v-if="warmGuardSelected" class="summary-field">
        <span>最温暖的守望等级（决定上限增长与阈值）</span>
        <select v-model.number="warmGuardLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>

      <label v-if="joyReunionSelected" class="summary-field">
        <span>最喜悦的重逢等级（守望伤害加成）</span>
        <select v-model.number="joyReunionLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="joyReunionSelected" class="summary-field">
        <span>当前魔灵数量（参与叠加的数量）</span>
        <input v-model.number="magicLingCount" type="number" min="0" max="30" step="1" />
      </label>
    </div>

    <div v-if="coreSelected" class="hero-summary-result">
      估算：非重聚阶段消耗的最大生命总量（%）
      <span class="hero-summary-highlight">{{ lifeConsumedPctTotal.toFixed(1) }}%</span>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：守望的暖风（核心）。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 守望状态：非重聚每秒获得 1 层暖风（上限可随最温暖的守望提升）
// 守望状态：重聚或非融合状态每秒失去 2 层暖风

const selectedSet = computed(() =>
  new Set((props.selectedTraits ?? []).map(s => (s ?? '').trim()).filter(Boolean))
)
const coreSelected = computed(() => selectedSet.value.has('守望的暖风'))
const sameRivalSelected = computed(() => selectedSet.value.has('同烈风共舞'))
const warmGuardSelected = computed(() => selectedSet.value.has('最温暖的守望'))
const joyReunionSelected = computed(() => selectedSet.value.has('最喜悦的重逢'))

// 最温暖的守望：
// “被融合的魔灵每消耗 (5/4.5/4.1/3.8/3.5)% 最大生命， +1 暖风层数上限，最多 (+15/+17/+19/+21/+23)”
const WARM_GUARD_THRESHOLDS = [5, 4.5, 4.1, 3.8, 3.5]
const WARM_GUARD_MAX_INC = [15, 17, 19, 21, 23]

// 同烈风共舞：
// “每次释放终极技能时，消耗 (2/3/3/4/4)% 最大生命，获得 (2/3/3/4/4) 层暖风”
const SAME_RIVAL_LAYERS = [2, 3, 3, 4, 4]

// 最喜悦的重逢：
// “守望状态期间，每有一个魔灵，被融合的魔灵额外 (+1/+2/+3/+4/+5)% 伤害（叠乘）”
const JOY_REUNION_PER_MAGICLING = [1, 2, 3, 4, 5]

const startWarmStacks = ref<number>(5)
const nonRegroupSeconds = ref<number>(4)
const regroupSeconds = ref<number>(0)

const sameRivalLevel = ref<number>(3)
const ultimateCount = ref<number>(0)

const warmGuardLevel = ref<number>(3)
const joyReunionLevel = ref<number>(3)
const magicLingCount = ref<number>(5)

const lifeConsumedPctTotal = computed(() => {
  if (!coreSelected.value) return 0
  // 非重聚：每秒消耗 20% 最大生命（文本固定）
  const base = 20 * Math.max(0, nonRegroupSeconds.value || 0)
  // 大招：额外消耗
  const lvIdx = Math.min(Math.max(sameRivalLevel.value || 1, 1), 5) - 1
  const lifePerUltimate = [2, 3, 3, 4, 4][lvIdx] || 0
  const add = sameRivalSelected.value ? lifePerUltimate * Math.max(0, ultimateCount.value || 0) : 0
  return base + add
})

const computedWarmMax = computed(() => {
  if (!coreSelected.value) return 10
  if (!warmGuardSelected.value) return 10
  const lvIdx = Math.min(Math.max(warmGuardLevel.value || 1, 1), 5) - 1
  const threshold = WARM_GUARD_THRESHOLDS[lvIdx] || 0
  const maxInc = WARM_GUARD_MAX_INC[lvIdx] || 0
  const consumed = Math.max(0, lifeConsumedPctTotal.value || 0)
  if (threshold <= 0) return 10
  const inc = Math.min(maxInc, Math.floor(consumed / threshold))
  return 10 + inc
})

const currentWarmStacks = computed(() => {
  if (!coreSelected.value) return 0
  const maxStacks = computedWarmMax.value
  let stacks = Math.min(Math.max(startWarmStacks.value || 0, 0), maxStacks)

  // 非重聚：每秒 +1
  stacks += Math.max(0, nonRegroupSeconds.value || 0)
  stacks = Math.min(stacks, maxStacks)

  // 大招：每次 +（2/3/3/4/4）
  if (sameRivalSelected.value) {
    const lvIdx = Math.min(Math.max(sameRivalLevel.value || 1, 1), 5) - 1
    const addPer = SAME_RIVAL_LAYERS[lvIdx] || 0
    stacks += addPer * Math.max(0, ultimateCount.value || 0)
  }
  stacks = Math.min(stacks, maxStacks)

  // 重聚：每秒 -2
  stacks -= 2 * Math.max(0, regroupSeconds.value || 0)
  stacks = Math.max(0, stacks)

  return stacks
})

const joyPerPct = computed(() => {
  if (!coreSelected.value || !joyReunionSelected.value) return 0
  const lvIdx = Math.min(Math.max(joyReunionLevel.value || 1, 1), 5) - 1
  return JOY_REUNION_PER_MAGICLING[lvIdx] || 0
})

const extraDamagePct = computed(() => {
  if (!coreSelected.value || !joyReunionSelected.value) return 0
  const count = Math.max(0, magicLingCount.value || 0)
  return count * joyPerPct.value
})
</script>

