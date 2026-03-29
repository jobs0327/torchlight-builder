<template>
  <div>
    <div class="hero-summary-title">自爆伤害与召唤物增伤参考（指挥官 莫托｜冲锋征召）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      期望自毁程序自爆伤害增幅（近似）：
      <span class="hero-summary-highlight">
        约 +{{ totalSelfDestructBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      来自“自毁程序伤害/召唤物伤害”的主要加成项拆分：
      <span class="hero-summary-highlight">
        召唤物增伤 +{{ pickupDamageBonusPct.toFixed(1) }}% ，自毁伤害额外 +{{ selfDestructDamageBonusPct.toFixed(1) }}% ，生命护盾阈值额外 +{{ lifeShieldBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="pickupSelected" class="summary-field">
        <span>前仆后继等级（拾取->召唤物伤害）</span>
        <select v-model.number="pickupTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="pickupSelected" class="summary-field">
        <span>拾取的机械零件次数（用于加成）</span>
        <input v-model.number="pickupCount" type="number" min="0" max="50" step="1" />
      </label>

      <label v-if="sabotageSelected" class="summary-field">
        <span>游击战术等级（拾取->自毁伤害）</span>
        <select v-model.number="sabotageTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>

      <label v-if="sacrificeSelected" class="summary-field">
        <span>捐躯赴难等级（生命/护盾阈值）</span>
        <select v-model.number="sacrificeTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="sacrificeSelected" class="summary-field">
        <span>智械最大生命或护盾值（用于阈值计算）</span>
        <input v-model.number="lifeOrShieldValue" type="number" min="0" step="10" />
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：冲锋征召（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('冲锋征召'))
const pickupSelected = computed(() => selectedSet.value.has('前仆后继'))
const sabotageSelected = computed(() => selectedSet.value.has('游击战术'))
const sacrificeSelected = computed(() => selectedSet.value.has('捐躯赴难'))

// 冲锋征召：额外 +20% 由自毁程序引发的自爆伤害
const BASE_SELF_DEStruct = 20

// 前仆后继：每拾取一个机械零件，额外 (+3/3.5/4/4.5/5)% 召唤物伤害，最多叠加 10 次
const PICKUP_SUMMON_DAMAGE_PER = [3, 3.5, 4, 4.5, 5]
const PICKUP_SUMMON_DAMAGE_CAP = 10

// 游击战术：每拾取一个机械零件，额外 +3% 自毁程序伤害，最多叠加 (10/12/15/18/20) 次
const SABOTAGE_SELF_DEStruct_DAMAGE_CAP = [10, 12, 15, 18, 20]
const SELF_DEStruct_DAMAGE_PER_PICKUP = 3

// 捐躯赴难：智械召唤物每有 (+70/+60/+50/+45/+40)最大生命或护盾，自毁程序引发的自爆额外 +1% 伤害
const LIFE_SHIELD_THRESHOLD = [70, 60, 50, 45, 40]
const LIFE_SHIELD_BONUS_PER_THRESHOLD = 1

const pickupTraitLevel = ref<number>(3)
const pickupCount = ref<number>(10)

const sabotageTraitLevel = ref<number>(3)

const sacrificeTraitLevel = ref<number>(3)
const lifeOrShieldValue = ref<number>(500)

const pickupDamageBonusPct = computed(() => {
  if (!coreSelected.value || !pickupSelected.value) return 0
  const lvIdx = Math.min(Math.max(pickupTraitLevel.value || 1, 1), 5) - 1
  const per = PICKUP_SUMMON_DAMAGE_PER[lvIdx] || 0
  const stacks = Math.min(PICKUP_SUMMON_DAMAGE_CAP, Math.max(0, pickupCount.value || 0))
  return stacks * per
})

const selfDestructDamageBonusPct = computed(() => {
  if (!coreSelected.value || !sabotageSelected.value) return 0
  const lvIdx = Math.min(Math.max(sabotageTraitLevel.value || 1, 1), 5) - 1
  const cap = SABOTAGE_SELF_DEStruct_DAMAGE_CAP[lvIdx] || 0
  const stacks = Math.min(cap, Math.max(0, pickupCount.value || 0))
  return stacks * SELF_DEStruct_DAMAGE_PER_PICKUP
})

const lifeShieldBonusPct = computed(() => {
  if (!coreSelected.value || !sacrificeSelected.value) return 0
  const lvIdx = Math.min(Math.max(sacrificeTraitLevel.value || 1, 1), 5) - 1
  const threshold = LIFE_SHIELD_THRESHOLD[lvIdx] || 0
  const v = Math.max(0, lifeOrShieldValue.value || 0)
  if (threshold <= 0) return 0
  const stacks = Math.floor(v / threshold)
  return stacks * LIFE_SHIELD_BONUS_PER_THRESHOLD
})

const totalSelfDestructBonusPct = computed(() => {
  if (!coreSelected.value) return 0
  // 近似：将各词条额外%直接加总到一个“总增幅”
  return BASE_SELF_DEStruct + pickupDamageBonusPct.value + selfDestructDamageBonusPct.value + lifeShieldBonusPct.value
})
</script>

