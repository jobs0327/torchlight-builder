<template>
  <div>
    <div class="hero-summary-title">祝福层数与神域增伤参考（神谕者 希雅｜众神之化身）</div>

    <!-- 满配参考 -->
    <div v-if="coreSelected && shenquanSelected && shenliSelected" class="hero-summary-line">
      神域外 · 对生命健康敌人（灵动祝福 20 层，三种祝福都满层，相关特性 5 级）：
      <span class="hero-summary-highlight">
        约 {{ fullHealthyDamage.toFixed(1) }}% 伤害（约 {{ (1 + fullHealthyDamage / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-if="coreSelected && shenquanSelected && shenyuSelected && huashenSelected" class="hero-summary-line">
      神域内 · 对生命濒危敌人（坚韧祝福 20 层，三种祝福都满层，相关特性 5 级）：
      <span class="hero-summary-highlight">
        约 {{ fullDangerDamage.toFixed(1) }}% 伤害（约 {{ (1 + fullDangerDamage / 100).toFixed(2) }} 倍）
      </span>
    </div>

    <!-- 配置表单 -->
    <div class="hero-summary-form">
      <label v-if="coreSelected" class="summary-field">
        <span>当前聚能祝福层数</span>
        <input v-model.number="qLayers" type="number" min="0" max="40" />
      </label>
      <label v-if="coreSelected" class="summary-field">
        <span>当前灵动祝福层数</span>
        <input v-model.number="mLayers" type="number" min="0" max="40" />
      </label>
      <label v-if="coreSelected" class="summary-field">
        <span>当前坚韧祝福层数</span>
        <input v-model.number="rLayers" type="number" min="0" max="40" />
      </label>
      <label v-if="coreSelected" class="summary-field">
        <span>已达到层数上限的祝福种类数</span>
        <input v-model.number="cappedTypes" type="number" min="0" max="3" />
      </label>
    </div>

    <div class="hero-summary-form">
      <label v-if="shenquanSelected" class="summary-field">
        <span>神权等级</span>
        <select v-model.number="shenquanLevel">
          <option v-for="n in 5" :key="`sq-${n}`" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="shenliSelected" class="summary-field">
        <span>神力流转等级</span>
        <select v-model.number="shenliLevel">
          <option v-for="n in 5" :key="`sl-${n}`" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="shenyuSelected" class="summary-field">
        <span>神域威能等级</span>
        <select v-model.number="shenyuLevel">
          <option v-for="n in 5" :key="`sy-${n}`" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="huashenSelected" class="summary-field">
        <span>化身降身等级</span>
        <select v-model.number="huashenLevel">
          <option v-for="n in 5" :key="`hs-${n}`" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>

    <!-- 当前配置结果 -->
    <div v-if="coreSelected" class="hero-summary-result">
      神域外 · 对生命健康敌人（只计灵动系相关）：
      <span class="hero-summary-highlight">
        约 {{ currentHealthyDamage.toFixed(1) }}% 伤害（约 {{ (1 + currentHealthyDamage / 100).toFixed(2) }} 倍）
      </span>
      <span class="hero-summary-note">
        （包含众神之化身 灵动祝福对生命健康敌人的伤害、神权 满层祝福的额外伤害、神力流转 在神域外按祝福层数提供的伤害）
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-result">
      神域内 · 对生命濒危敌人（只计坚韧系相关）：
      <span class="hero-summary-highlight">
        约 {{ currentDangerDamage.toFixed(1) }}% 伤害（约 {{ (1 + currentDangerDamage / 100).toFixed(2) }} 倍）
      </span>
      <span class="hero-summary-note">
        （包含众神之化身 坚韧祝福对生命濒危敌人的伤害、神权 满层祝福的额外伤害、神域威能 神域内的额外伤害、化身降身
        按祝福总层数提供的神域内伤害）
      </span>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：众神之化身（核心）。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 神权：每种满层祝福叠乘额外伤害（近似按总和处理）
const SHENQUAN_VALUES = [10, 12, 14, 16, 19]
// 神力流转：神域外每层祝福提供的伤害
const SHENLI_PER_BLESS = [0.5, 0.8, 1.1, 1.4, 1.7]
// 神域威能：神域内对敌人额外伤害
const SHENYU_VALUES = [20, 26, 32, 38, 45]
// 化身降身：按总祝福层数提供神域内伤害
const HUASHEN_PER_BLESS = [1, 1.25, 1.5, 1.75, 2]

const qLayers = ref<number>(4) // 聚能祝福（默认 4 层）
const mLayers = ref<number>(4) // 灵动祝福（默认 4 层）
const rLayers = ref<number>(4) // 坚韧祝福（默认 4 层）
// 默认情况下当前层数较低，按“未触及层数上限”处理更符合预期
const cappedTypes = ref<number>(0)

const shenquanLevel = ref<number>(5)
const shenliLevel = ref<number>(5)
const shenyuLevel = ref<number>(5)
const huashenLevel = ref<number>(5)

const totalBlessings = computed(() => Math.max(0, (qLayers.value || 0) + (mLayers.value || 0) + (rLayers.value || 0)))

function calcHealthyDamage(
  m: number,
  total: number,
  capped: number,
  shenquanLv: number,
  shenliLv: number,
  hasCore: boolean,
  hasShenquan: boolean,
  hasShenli: boolean
): number {
  const mClamped = Math.min(Math.max(m, 0), 20)
  const core = hasCore ? mClamped * 7 : 0 // 每层灵动祝福对生命健康敌人 +7% 伤害，最多 20 层

  const perBless = hasShenli ? SHENLI_PER_BLESS[Math.min(Math.max(shenliLv, 1), 5) - 1] || 0 : 0
  const blessCount = Math.min(Math.max(total, 0), 40)
  const shenli = hasShenli ? blessCount * perBless : 0

  const sqPer = hasShenquan ? SHENQUAN_VALUES[Math.min(Math.max(shenquanLv, 1), 5) - 1] || 0 : 0
  const sq = hasShenquan ? Math.min(Math.max(capped, 0), 3) * sqPer : 0

  return core + shenli + sq
}

function calcDangerDamage(
  r: number,
  total: number,
  capped: number,
  shenquanLv: number,
  shenyuLv: number,
  huashenLv: number,
  hasCore: boolean,
  hasShenquan: boolean,
  hasShenyu: boolean,
  hasHuashen: boolean
): number {
  const rClamped = Math.min(Math.max(r, 0), 20)
  const core = hasCore ? rClamped * 7 : 0 // 每层坚韧祝福对生命濒危敌人 +7% 伤害，最多 20 层

  const sy = hasShenyu ? SHENYU_VALUES[Math.min(Math.max(shenyuLv, 1), 5) - 1] || 0 : 0

  const perBless = hasHuashen ? HUASHEN_PER_BLESS[Math.min(Math.max(huashenLv, 1), 5) - 1] || 0 : 0
  const blessCount = Math.min(Math.max(total, 0), 40)
  const hs = hasHuashen ? blessCount * perBless : 0

  const sqPer = hasShenquan ? SHENQUAN_VALUES[Math.min(Math.max(shenquanLv, 1), 5) - 1] || 0 : 0
  const sq = hasShenquan ? Math.min(Math.max(capped, 0), 3) * sqPer : 0

  return core + sy + hs + sq
}

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('众神之化身'))
const shenquanSelected = computed(() => selectedSet.value.has('神权'))
const shenliSelected = computed(() => selectedSet.value.has('神力流转'))
const shenyuSelected = computed(() => selectedSet.value.has('神域威能'))
const huashenSelected = computed(() => selectedSet.value.has('化身降身'))

// 满配参考：假设三种祝福都在 20 层且都达上限
const fullHealthyDamage = computed(() =>
  coreSelected.value && shenquanSelected.value && shenliSelected.value
    ? calcHealthyDamage(20, 60, 3, 5, 5, true, true, true)
    : 0
)

const fullDangerDamage = computed(() =>
  coreSelected.value && shenquanSelected.value && shenyuSelected.value && huashenSelected.value
    ? calcDangerDamage(20, 60, 3, 5, 5, 5, true, true, true, true)
    : 0
)

const currentHealthyDamage = computed(() =>
  coreSelected.value
    ? calcHealthyDamage(
        mLayers.value || 0,
        totalBlessings.value,
        cappedTypes.value || 0,
        shenquanLevel.value || 1,
        shenliLevel.value || 1,
        true,
        shenquanSelected.value,
        shenliSelected.value
      )
    : 0
)

const currentDangerDamage = computed(() =>
  coreSelected.value
    ? calcDangerDamage(
        rLayers.value || 0,
        totalBlessings.value,
        cappedTypes.value || 0,
        shenquanLevel.value || 1,
        shenyuLevel.value || 1,
        huashenLevel.value || 1,
        true,
        shenquanSelected.value,
        shenyuSelected.value,
        huashenSelected.value
      )
    : 0
)
</script>

