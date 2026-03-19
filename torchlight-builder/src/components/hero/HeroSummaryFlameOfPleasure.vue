<template>
  <div>
    <div class="hero-summary-title">炼狱范围伤害参考（冰焰 吉玛｜欢愉之焰）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（炼狱持续 10 秒，无尽极刑 5 级，狱火沉沦 5 级，极乐狂宴 5 级，裙下之臣 5 级）：
      <span class="hero-summary-highlight">
        对所有伤害约 {{ flameFullGeneric.toFixed(1) }}% 伤害（约 {{ (1 + flameFullGeneric / 100).toFixed(2) }} 倍），
        对火焰伤害约 {{ flameFullFire.toFixed(1) }}% 伤害（约 {{ (1 + flameFullFire / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：欢愉之焰、狱火沉沦、裙下之臣。
    </div>

    <div class="hero-summary-form">
      <label v-if="coreSelected" class="summary-field">
        <span>炼狱持续秒数</span>
        <input v-model.number="flameSeconds" type="number" min="0" max="20" />
      </label>
      <label v-if="yuhuoSelected" class="summary-field">
        <span>狱火沉沦等级</span>
        <select v-model.number="flameYuhuoLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="skirtSelected" class="summary-field">
        <span>裙下之臣等级</span>
        <select v-model.number="flameSkirtLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前炼狱中：
        <span class="hero-summary-highlight">
          对所有伤害约 {{ flameCurrentGeneric.toFixed(1) }}% 伤害（约 {{ (1 + flameCurrentGeneric / 100).toFixed(2) }} 倍），
          对火焰伤害约 {{ flameCurrentFire.toFixed(1) }}% 伤害（约 {{ (1 + flameCurrentFire / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含欢愉之焰核心 +45% 敌人承受伤害、狱火沉沦 随时间累积伤害、裙下之臣 对火焰伤害的额外承受效果；未计入炽热诅咒与处决机制的间接增益）
        </span>
      </template>
      <div v-else class="hero-summary-note" style="display: block;">
        需要勾选上述三项后再计算。
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

// 冰焰 吉玛｜欢愉之焰 炼狱伤害
const FLAME_YUHUO_PER = [6, 7, 8, 9, 10] // 狱火沉沦 每秒伤害%
const FLAME_SKIRT_FIRE = [30, 35, 40, 45, 50] // 裙下之臣 敌人额外受到火焰伤害

const flameSeconds = ref<number>(10)
const flameYuhuoLevel = ref<number>(5)
const flameSkirtLevel = ref<number>(5)

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('欢愉之焰'))
const yuhuoSelected = computed(() => selectedSet.value.has('狱火沉沦'))
const skirtSelected = computed(() => selectedSet.value.has('裙下之臣'))
const canCalc = computed(() => coreSelected.value && yuhuoSelected.value && skirtSelected.value)

function calcFlameBonus(seconds: number, yuhuoLv: number, skirtLv: number) {
  const baseTaken = 45 // 欢愉之焰：炼狱内敌人额外 +45% 受到的伤害
  const perSec = FLAME_YUHUO_PER[Math.min(Math.max(yuhuoLv, 1), 5) - 1] || 0
  const s = Math.max(0, seconds || 0)
  const yuhuo = s * perSec
  const generic = baseTaken + yuhuo

  const skirt = FLAME_SKIRT_FIRE[Math.min(Math.max(skirtLv, 1), 5) - 1] || 0
  const extraFire = skirt + 30 // 文本中额外 +30% 火焰伤害一行，合并计算
  const fire = generic + extraFire
  return { generic, fire }
}

const flameFullGeneric = computed(() => (canCalc.value ? calcFlameBonus(10, 5, 5).generic : 0))
const flameFullFire = computed(() => (canCalc.value ? calcFlameBonus(10, 5, 5).fire : 0))

const flameCurrentGeneric = computed(() =>
  canCalc.value
    ? calcFlameBonus(
        flameSeconds.value || 0,
        flameYuhuoLevel.value || 1,
        flameSkirtLevel.value || 1
      ).generic
    : 0
)
const flameCurrentFire = computed(() =>
  canCalc.value
    ? calcFlameBonus(
        flameSeconds.value || 0,
        flameYuhuoLevel.value || 1,
        flameSkirtLevel.value || 1
      ).fire
    : 0
)
</script>

