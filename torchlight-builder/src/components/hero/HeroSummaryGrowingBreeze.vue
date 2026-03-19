<template>
  <div>
    <div class="hero-summary-title">润物层数与强化几率参考（遗世魔灵 伊瑞斯｜生长的微风）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      润物伤害增幅：
      <span class="hero-summary-highlight">
        有润物（≥1 层）时，额外 +30% 该次技能伤害
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      当前润物层数：<span class="hero-summary-highlight">{{ runoLayers }} 层</span>，
      下一次释放技能丢失 1 层的概率（近似）：
      <span class="hero-summary-highlight">{{ lossProbPct.toFixed(1) }}%</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      在 5 米内无敌人（且有润物）时：移动速度 +70%
      <span class="hero-summary-highlight" v-if="noEnemies5m">（已开启）</span>
      <span class="hero-summary-highlight" v-else>（未开启）</span>
    </div>

    <div v-if="coreSelected && embraceWorldSelected" class="hero-summary-line">
      拥抱世界吧（强化技能使用几率）：
      <span class="hero-summary-highlight">+{{ enhancedSkillChancePct.toFixed(1) }}%</span>
      <span class="hero-summary-note">(按火焰/冰冷/闪电抗性合计，并受最大值上限影响)</span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label class="summary-field">
        <span>当前润物层数（0-10）</span>
        <input v-model.number="runoLayers" type="number" min="0" max="10" step="1" />
      </label>
      <label class="summary-field">
        <span>魔灵接下来释放技能次数（用于估算剩余润物）</span>
        <input v-model.number="skillCasts" type="number" min="0" max="20" step="1" />
      </label>
      <label class="summary-field">
        <span>接下来是否满足“5 米内无敌人”</span>
        <select v-model="noEnemies5m">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>

      <label v-if="embraceWorldSelected" class="summary-field">
        <span>拥抱世界吧等级</span>
        <select v-model.number="embraceWorldLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="embraceWorldSelected" class="summary-field">
        <span>火焰抗性（%）</span>
        <input v-model.number="resFirePct" type="number" min="0" max="100" step="1" />
      </label>
      <label v-if="embraceWorldSelected" class="summary-field">
        <span>冰冷抗性（%）</span>
        <input v-model.number="resColdPct" type="number" min="0" max="100" step="1" />
      </label>
      <label v-if="embraceWorldSelected" class="summary-field">
        <span>闪电抗性（%）</span>
        <input v-model.number="resLightningPct" type="number" min="0" max="100" step="1" />
      </label>
    </div>

    <div v-if="coreSelected" class="hero-summary-result">
      估算：释放 {{ skillCasts }} 次技能后，润物期望剩余层数：
      <span class="hero-summary-highlight">{{ expectedStacksAfter.toFixed(2) }} 层</span>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：生长的微风（核心）。
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
const coreSelected = computed(() => selectedSet.value.has('生长的微风'))
const embraceWorldSelected = computed(() => selectedSet.value.has('拥抱世界吧'))

// 润物：
// - 有润物时，使用技能额外 +30% 该次技能伤害（上限 10 层）
// - 释放技能时：+30% 几率失去 1 层润物
// - 且：每有一层润物，使用技能时 +8% 几率失去 1 层润物
const MAX_LAYERS = 10

const runoLayers = ref<number>(4)
const skillCasts = ref<number>(3)
const noEnemies5m = ref<boolean>(true)

// 拥抱世界吧：
// 每有 1% 火焰/冰冷/闪电抗性 -> 对应魔灵 +1% 强化技能使用几率（合计受最大值上限影响）
const EMBRACE_WORLD_MAX = [28, 36, 44, 52, 60]
const embraceWorldLevel = ref<number>(5)

const resFirePct = ref<number>(30)
const resColdPct = ref<number>(30)
const resLightningPct = ref<number>(30)

const lossProbPct = computed(() => {
  if (!coreSelected.value) return 0
  const k = Math.min(Math.max(runoLayers.value || 0, 0), MAX_LAYERS)
  // p = 30% + 8% * k
  const p = 30 + 8 * k
  return Math.min(100, Math.max(0, p))
})

const expectedStacksAfter = computed(() => {
  if (!coreSelected.value) return 0
  const initial = Math.min(Math.max(runoLayers.value || 0, 0), MAX_LAYERS)
  const casts = Math.min(Math.max(skillCasts.value || 0, 0), 20)

  // Markov 链：k -> k-1 以 p(k) 发生，k 不变以 1-p(k) 发生
  let dist: number[] = Array.from({ length: MAX_LAYERS + 1 }, (_, i) => (i === initial ? 1 : 0))
  for (let t = 0; t < casts; t++) {
    const next = new Array(MAX_LAYERS + 1).fill(0)
    for (let k = 0; k <= MAX_LAYERS; k++) {
      const cur = dist[k]
      if (cur <= 0) continue
      if (k === 0) {
        next[0] += cur
        continue
      }
      const p = Math.min(1, (0.3 + 0.08 * k)) // 30% + 8%*k
      next[k] += cur * (1 - p)
      next[k - 1] += cur * p
    }
    dist = next
  }

  let exp = 0
  for (let k = 0; k <= MAX_LAYERS; k++) exp += k * dist[k]
  return exp
})

const enhancedSkillChancePct = computed(() => {
  if (!coreSelected.value || !embraceWorldSelected.value) return 0
  const lvIdx = Math.min(Math.max(embraceWorldLevel.value || 1, 1), 5) - 1
  const maxCap = EMBRACE_WORLD_MAX[lvIdx] || 0
  const sumRes = Math.max(0, resFirePct.value || 0) + Math.max(0, resColdPct.value || 0) + Math.max(0, resLightningPct.value || 0)
  // 每 1% 抗性贡献 1% 几率，按 maxCap 截断
  return Math.min(maxCap, sumRes)
})
</script>

