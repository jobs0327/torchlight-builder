<template>
  <div>
    <div class="hero-summary-title">幻象施法频率与伤害参考（时空见证者 尤加｜时空幻象）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      施法频率提升（相对基础）：
      <span class="hero-summary-highlight">
        约 +{{ totalFreqBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      对应的幻象平均施法间隔（基础 1.5 秒）：
      <span class="hero-summary-highlight">
        {{ illusionIntervalSeconds.toFixed(2) }} 秒
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      伤害增幅（仅汇总词条明确给出的“幻象伤害/你与幻象伤害额外百分比”）：
      <span class="hero-summary-highlight">
        约 +{{ totalIllusionDamageBonus.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="freqSelected" class="summary-field">
        <span>咱俩真棒等级（频率系数）</span>
        <select v-model.number="freqTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="freqSelected" class="summary-field">
        <span>冷却回复速度加成（%）</span>
        <input v-model.number="cooldownRecoveryPct" type="number" min="0" step="1" />
      </label>
      <label v-if="castSpeedSelected" class="summary-field">
        <span>搞快点等级（施法速度->伤害）</span>
        <select v-model.number="castSpeedTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="castSpeedSelected" class="summary-field">
        <span>施法速度加成（%）</span>
        <input v-model.number="castSpeedBonusPct" type="number" min="0" step="1" />
      </label>
      <label v-if="blueSelected" class="summary-field">
        <span>去码头等级（频率->伤害）</span>
        <select v-model.number="blueTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="manaDrainSelected" class="summary-field">
        <span>我没蓝了等级（消耗魔力->伤害）</span>
        <select v-model.number="manaDrainTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="manaDrainSelected" class="summary-field">
        <span>幻象消耗魔力次数（0-10）</span>
        <input v-model.number="manaDrainStacks" type="number" min="0" max="10" />
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：时空幻象（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('时空幻象'))
const freqSelected = computed(() => selectedSet.value.has('咱俩真棒'))
const castSpeedSelected = computed(() => selectedSet.value.has('搞快点搞快点'))
const blueSelected = computed(() => selectedSet.value.has('去码头整点蓝条'))
const manaDrainSelected = computed(() => selectedSet.value.has('我没蓝了'))

// 关键词条数值：
// 咱俩真棒：+60% 时空幻象的施法频率；每有 +5% 冷却回复速度，(+5/+7/+9/+11/+13)% 时空幻象施法频率
const FREQ_BASE_BONUS = 60 // 固定 +60%
const FREQ_CDR_COEF = [5, 7, 9, 11, 13] // 每 +5% 冷却回复速度 -> 额外频率%

// 搞快点：施法速度加成的 (+50/+55/+60/+65/+70)% 同样作用于幻象额外伤害，上限 300%
const CAST_SPEED_DAMAGE_COEF = [50, 55, 60, 65, 70]
const CAST_SPEED_DAMAGE_CAP = 300

// 去码头：每 +4% 时空幻象的施法频率，额外 (+1/1.15/1.3/1.45/1.6)% 时空幻象伤害
const FREQ_TO_DAMAGE_COEF = [1, 1.15, 1.3, 1.45, 1.6]

// 我没蓝了：每次消耗魔力，额外 (+5/6.3/7.5/8.8/10)% 你和时空幻象伤害，最多叠加 10 次
const MANA_DRAIN_DAMAGE_COEF = [5, 6.3, 7.5, 8.8, 10]

const freqTraitLevel = ref<number>(5)
const cooldownRecoveryPct = ref<number>(0) // 比如 10 表示 +10% 冷却回复速度

const castSpeedTraitLevel = ref<number>(5)
const castSpeedBonusPct = ref<number>(150)

const blueTraitLevel = ref<number>(5)

const manaDrainTraitLevel = ref<number>(5)
const manaDrainStacks = ref<number>(6)

const totalFreqBonusPct = computed(() => {
  if (!coreSelected.value || !freqSelected.value) return 0
  const lvIdx = Math.min(Math.max(freqTraitLevel.value || 1, 1), 5) - 1
  const per = FREQ_CDR_COEF[lvIdx] || 0
  const steps = Math.max(0, cooldownRecoveryPct.value || 0) / 5
  const add = steps * per
  return FREQ_BASE_BONUS + add
})

const illusionIntervalSeconds = computed(() => {
  const base = 1.5
  const mul = 1 + totalFreqBonusPct.value / 100
  if (mul <= 0) return base
  return base / mul
})

const castSpeedExtraDamage = computed(() => {
  if (!coreSelected.value || !castSpeedSelected.value) return 0
  const lvIdx = Math.min(Math.max(castSpeedTraitLevel.value || 1, 1), 5) - 1
  const coef = CAST_SPEED_DAMAGE_COEF[lvIdx] || 0
  const raw = Math.max(0, castSpeedBonusPct.value || 0) * (coef / 100)
  return Math.min(raw, CAST_SPEED_DAMAGE_CAP)
})

const freqToDamageExtra = computed(() => {
  if (!coreSelected.value || !blueSelected.value) return 0
  const lvIdx = Math.min(Math.max(blueTraitLevel.value || 1, 1), 5) - 1
  const per4 = FREQ_TO_DAMAGE_COEF[lvIdx] || 0
  const units = Math.max(0, totalFreqBonusPct.value) / 4
  return units * per4
})

const manaDrainExtra = computed(() => {
  if (!coreSelected.value || !manaDrainSelected.value) return 0
  const lvIdx = Math.min(Math.max(manaDrainTraitLevel.value || 1, 1), 5) - 1
  const per = MANA_DRAIN_DAMAGE_COEF[lvIdx] || 0
  const stacks = Math.min(10, Math.max(0, manaDrainStacks.value || 0))
  return stacks * per
})

const totalIllusionDamageBonus = computed(() => {
  // 说明：这是对词条“额外%”的直接加和，未融合基础技能倍率/额外触发次数等游戏细节。
  return castSpeedExtraDamage.value + freqToDamageExtra.value + manaDrainExtra.value
})
</script>

