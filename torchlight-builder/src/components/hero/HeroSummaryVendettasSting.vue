<template>
  <div>
    <div class="hero-summary-title">寻仇之刺数值参考（猫眼 艾瑞卡｜寻仇之刺）</div>

    <div class="hero-summary-form">
      <div v-if="!anySelected" class="hero-summary-note" style="display: block; margin-bottom: 8px;">
        请先在左侧勾选要计算的特性。
      </div>

      <div class="hero-summary-line" style="margin-bottom: 8px;">天赋等级</div>
      <label class="summary-field" v-if="shuangrenSelected">
        <span>双刃齐下</span>
        <select v-model.number="shuangrenLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field" v-if="xiushouSelected">
        <span>袖手悠游</span>
        <select v-model.number="xiushouLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field" v-if="jiyingSelected">
        <span>疾影潜踪</span>
        <select v-model.number="jiyingLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field" v-if="maobukeSelected">
        <span>猫不可忍</span>
        <select v-model.number="maobukeLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field" v-if="mingxuanSelected">
        <span>命悬一线</span>
        <select v-model.number="mingxuanLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>

      <div class="hero-summary-line" style="margin: 12px 0 8px;">状态与面板</div>
      <label class="summary-field">
        <span>双持</span>
        <select v-model="isDualWield">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label class="summary-field">
        <span>双持武器类型相同</span>
        <select v-model="sameWeaponType">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label class="summary-field">
        <span>拥有迅捷</span>
        <select v-model="hasSwift">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label class="summary-field">
        <span>目标为劲敌</span>
        <select v-model="targetIsElite">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
      <label class="summary-field">
        <span>有效暴击率 %</span>
        <input v-model.number="effectiveCritPct" type="number" min="0" max="200" />
      </label>
      <label class="summary-field">
        <span>溢出暴击率 %</span>
        <input v-model.number="overflowCritPct" type="number" min="0" max="200" />
      </label>
      <label class="summary-field">
        <span>灵动祝福层数</span>
        <input v-model.number="blessingStacks" type="number" min="0" max="20" />
      </label>
      <label class="summary-field">
        <span>距离敌人 米</span>
        <input v-model.number="distanceToEnemy" type="number" min="0" max="10" step="0.5" />
      </label>
    </div>

    <div class="hero-summary-result">
      <div v-if="shuangrenSelected" class="hero-summary-line">
        双刃齐下（双持时）额外攻击伤害：
        <span class="hero-summary-highlight">{{ shuangrenExtraDmg }}%</span>
        <span class="hero-summary-note" v-if="!isDualWield">（需双持）</span>
      </div>
      <div v-if="xiushouSelected" class="hero-summary-line">
        迅捷下寻仇额外攻速：
        <span class="hero-summary-highlight">{{ xiushouVendettaAtkSpeed }}%</span>
        <span class="hero-summary-note" v-if="!hasSwift">（需迅捷）</span>
      </div>
      <div v-if="jiyingSelected" class="hero-summary-line">
        疾影潜踪对劲敌额外伤害：
        <span class="hero-summary-highlight">{{ jiyingEliteExtra }}%</span>
        <span class="hero-summary-note" v-if="!targetIsElite">（目标需为劲敌）</span>
      </div>
      <div v-if="jiyingSelected" class="hero-summary-line">
        疾影潜踪凌厉：持续 <span class="hero-summary-highlight">+333%</span>，效果 <span class="hero-summary-highlight">+99%</span>
      </div>
      <div v-if="maobukeSelected" class="hero-summary-line">
        猫不可忍：寻仇额外触发概率约 <span class="hero-summary-highlight">{{ maobukeP1.toFixed(1) }}%</span>（有效暴击），
        再额外 <span class="hero-summary-highlight">{{ maobukeP2.toFixed(1) }}%</span>（溢出），
        期望额外次数 <span class="hero-summary-highlight">{{ maobukeExpected.toFixed(2) }}</span>
      </div>
      <div class="hero-summary-line" v-if="maobukeSelected && isDualWield">
        猫不可忍双持：<span v-if="sameWeaponType" class="hero-summary-highlight">+200 攻击暴击值</span>
        <span v-else class="hero-summary-highlight">暴击额外 +20% 攻击伤害</span>
      </div>
      <div v-if="mingxuanSelected" class="hero-summary-line">
        命悬一线凌厉效果（灵动祝福）：<span class="hero-summary-highlight">+{{ mingxuanLingliBonus }}%</span>（上限 {{ mingxuanCap }} 层）
      </div>
      <div v-if="mingxuanSelected" class="hero-summary-line">
        命悬一线距离受伤增幅：<span class="hero-summary-highlight">+{{ distanceDmgTaken }}%</span> 受到的伤害
      </div>
      <span class="hero-summary-note" style="display: block; margin-top: 8px;">
        （公式按天赋描述线性近似，实际游戏可能有取整与叠加规则差异）
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  // 来自左侧选择：对同 requiredLevel 互斥选择后的特性名称列表
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 双刃齐下 1–5 级：额外攻击伤害 %
const SHUANGREN_VALUES = [25, 30, 35, 40, 45]
// 袖手悠游 1–5 级：迅捷下寻仇额外攻速 %（等级1 无加成）
const XIUSHOU_ATK_SPEED = [0, 5, 10, 15, 20]
// 疾影潜踪 1–5 级：对劲敌额外伤害 %
const JIYING_ELITE = [30, 45, 60, 75, 90]
// 猫不可忍：每 X% 有效暴击率 → 1% 概率额外触发
const MAOBUKE_CRIT_THRESHOLD = [5, 4, 3, 2.5, 2]
// 命悬一线：灵动祝福上限层数
const MINGXUAN_CAP = [6, 7, 8, 9, 10]

const shuangrenLevel = ref<number>(5)
const xiushouLevel = ref<number>(5)
const jiyingLevel = ref<number>(5)
const maobukeLevel = ref<number>(5)
const mingxuanLevel = ref<number>(5)

const isDualWield = ref<boolean>(true)
const sameWeaponType = ref<boolean>(true)
const hasSwift = ref<boolean>(true)
const targetIsElite = ref<boolean>(true)
const effectiveCritPct = ref<number>(50)
const overflowCritPct = ref<number>(0)
const blessingStacks = ref<number>(6)
const distanceToEnemy = ref<number>(2)

function pick<T>(arr: T[], level: number): T {
  const lv = Math.min(Math.max(level || 1, 1), 5)
  return arr[lv - 1] ?? arr[0]
}

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))

const shuangrenSelected = computed(() => selectedSet.value.has('双刃齐下'))
const xiushouSelected = computed(() => selectedSet.value.has('袖手悠游'))
const jiyingSelected = computed(() => selectedSet.value.has('疾影潜踪'))
const maobukeSelected = computed(() => selectedSet.value.has('猫不可忍'))
const mingxuanSelected = computed(() => selectedSet.value.has('命悬一线'))

const anySelected = computed(
  () =>
    shuangrenSelected.value ||
    xiushouSelected.value ||
    jiyingSelected.value ||
    maobukeSelected.value ||
    mingxuanSelected.value
)

const shuangrenExtraDmg = computed(() => {
  if (!shuangrenSelected.value) return 0
  if (!isDualWield.value) return 0
  return pick(SHUANGREN_VALUES, shuangrenLevel.value)
})

const xiushouVendettaAtkSpeed = computed(() => {
  if (!xiushouSelected.value) return 0
  if (!hasSwift.value) return 0
  return pick(XIUSHOU_ATK_SPEED, xiushouLevel.value)
})

const jiyingEliteExtra = computed(() => {
  if (!jiyingSelected.value) return 0
  if (!targetIsElite.value) return 0
  return pick(JIYING_ELITE, jiyingLevel.value)
})

const maobukeThreshold = computed(() => pick(MAOBUKE_CRIT_THRESHOLD, maobukeLevel.value))

const maobukeP1 = computed(() => {
  if (!maobukeSelected.value) return 0
  const t = maobukeThreshold.value
  if (t <= 0) return 0
  const pct = Math.max(0, effectiveCritPct.value ?? 0)
  return Math.min(100, (pct / t) * 1)
})

const maobukeP2 = computed(() => {
  if (!maobukeSelected.value) return 0
  const overflow = Math.max(0, overflowCritPct.value ?? 0)
  return Math.min(100, (overflow / 0.5) * 1)
})

const maobukeExpected = computed(() => maobukeP1.value / 100 + maobukeP2.value / 100)

const mingxuanCap = computed(() => pick(MINGXUAN_CAP, mingxuanLevel.value))

const mingxuanLingliBonus = computed(() => {
  if (!mingxuanSelected.value) return 0
  const cap = mingxuanCap.value
  const stacks = Math.max(0, Math.min(cap, blessingStacks.value ?? 0))
  return stacks * 40
})

const distanceDmgTaken = computed(() => {
  if (!mingxuanSelected.value) return 0
  const d = distanceToEnemy.value ?? 5
  if (d <= 2) return 5
  if (d >= 5) return 0
  return Number((((5 - d) / 3) * 5).toFixed(1))
})
</script>
