<template>
  <div>
    <div class="hero-summary-title">超载增伤与期望伤害参考（指挥官 莫托｜号令征召）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      期望超载伤害增幅（近似）：
      <span class="hero-summary-highlight">
        约 +{{ totalOverloadDamageBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      已损生命带来的额外伤害（背水一战）：
      <span class="hero-summary-highlight">
        约 +{{ backwaterExtraDamagePct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="firstSelected" class="summary-field">
        <span>一鼓作气等级（首次超载效果额外%）</span>
        <select v-model.number="firstOverloadTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="firstSelected" class="summary-field">
        <span>是否在首次超载窗口计算</span>
        <select v-model="isFirstOverload">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>

      <label v-if="tongYuSelected" class="summary-field">
        <span>坚甲厉兵等级（统御值->超载效果）</span>
        <select v-model.number="tongYuTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="tongYuSelected" class="summary-field">
        <span>统御值（用于坚甲厉兵）</span>
        <input v-model.number="tongYuValue" type="number" min="0" step="1" />
      </label>

      <label v-if="consumeLifeSelected" class="summary-field">
        <span>破釜沉舟等级（消耗生命->超载效果）</span>
        <select v-model.number="consumeLifeTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="consumeLifeSelected" class="summary-field">
        <span>最近 1 秒内消耗生命值（%）</span>
        <input v-model.number="consumedLifePctLastSecond" type="number" min="0" max="100" step="1" />
      </label>

      <label v-if="backwaterSelected" class="summary-field">
        <span>背水一战等级（已损生命->额外伤害）</span>
        <select v-model.number="backwaterTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="backwaterSelected" class="summary-field">
        <span>已损生命百分比（0-100）</span>
        <input v-model.number="lostLifePct" type="number" min="0" max="100" step="1" />
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：号令征召（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('号令征召'))
const firstSelected = computed(() => selectedSet.value.has('一鼓作气'))
const tongYuSelected = computed(() => selectedSet.value.has('坚甲厉兵'))
const consumeLifeSelected = computed(() => selectedSet.value.has('破釜沉舟'))
const backwaterSelected = computed(() => selectedSet.value.has('背水一战'))

// 号令征召：超载提供额外 +60% 伤害
const BASE_OVERLOAD_DAMAGE = 60

// 一鼓作气：首次获得的超载额外 (+120/+155/+190/+225/+270)% 超载效果
const FIRST_OVERLOAD_EFFECT_EXTRA = [120, 155, 190, 225, 270]

// 坚甲厉兵：每拥有 5 点统御值，(+9/+11/+13/+15/+18)% 超载效果
const TONGYU_EFFECT_PER_5 = [9, 11, 13, 15, 18]

// 破釜沉舟：最近 1 秒内每消耗 5% 生命，(+10/+11/+12/+14/+15)% 受到的超载效果，最多叠加 20 次
const CONSUMED_LIFE_EFFECT_PER_5 = [10, 11, 12, 14, 15]
const CONSUMED_LIFE_MAX_STACKS = 20

// 背水一战：根据已损失的生命额外伤害，至多额外 (+25/+32/+40/+50/+60)% 伤害
const BACKWATER_MAX_EXTRA = [25, 32, 40, 50, 60]

const firstOverloadTraitLevel = ref<number>(3)
const isFirstOverload = ref<boolean>(true)

const tongYuTraitLevel = ref<number>(3)
const tongYuValue = ref<number>(50)

const consumeLifeTraitLevel = ref<number>(3)
const consumedLifePctLastSecond = ref<number>(20) // 例如 20% => 4 次消耗

const backwaterTraitLevel = ref<number>(3)
const lostLifePct = ref<number>(50)

const firstOverloadMultiplier = computed(() => {
  if (!coreSelected.value || !firstSelected.value) return 1
  const lvIdx = Math.min(Math.max(firstOverloadTraitLevel.value || 1, 1), 5) - 1
  const extra = isFirstOverload.value ? FIRST_OVERLOAD_EFFECT_EXTRA[lvIdx] || 0 : 0
  return 1 + extra / 100
})

const tongYuMultiplier = computed(() => {
  if (!coreSelected.value || !tongYuSelected.value) return 1
  const lvIdx = Math.min(Math.max(tongYuTraitLevel.value || 1, 1), 5) - 1
  const per = TONGYU_EFFECT_PER_5[lvIdx] || 0
  const stacks = Math.floor(Math.max(0, tongYuValue.value || 0) / 5)
  return 1 + (stacks * per) / 100
})

const consumedLifeMultiplier = computed(() => {
  if (!coreSelected.value || !consumeLifeSelected.value) return 1
  const lvIdx = Math.min(Math.max(consumeLifeTraitLevel.value || 1, 1), 5) - 1
  const per = CONSUMED_LIFE_EFFECT_PER_5[lvIdx] || 0
  const stacks = Math.min(CONSUMED_LIFE_MAX_STACKS, Math.floor(Math.max(0, consumedLifePctLastSecond.value || 0) / 5))
  return 1 + (stacks * per) / 100
})

const backwaterExtraDamagePct = computed(() => {
  if (!coreSelected.value || !backwaterSelected.value) return 0
  const lvIdx = Math.min(Math.max(backwaterTraitLevel.value || 1, 1), 5) - 1
  const maxExtra = BACKWATER_MAX_EXTRA[lvIdx] || 0
  const pct = Math.min(100, Math.max(0, lostLifePct.value || 0)) / 100
  return maxExtra * pct
})

const totalOverloadDamageBonusPct = computed(() => {
  if (!coreSelected.value) return 0
  // 近似：基础超载伤害% * 各“超载效果倍率”相乘，再把背水额外伤害直接加到总伤害增幅中
  const overloadCore = BASE_OVERLOAD_DAMAGE * firstOverloadMultiplier.value * tongYuMultiplier.value * consumedLifeMultiplier.value
  return overloadCore + backwaterExtraDamagePct.value
})
</script>

