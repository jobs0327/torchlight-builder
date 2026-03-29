<template>
  <div>
    <div class="hero-summary-title">腐蚀伤害与腐蚀爆炸参考（神谕者 希雅｜渎神）</div>

    <div v-if="coreSelected && corrosionSelected" class="hero-summary-line">
      腐蚀伤害提升：
      <span class="hero-summary-highlight">
        约 +{{ corrosionDamageBonus.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected && corrosionSelected" class="hero-summary-line">
      目标被击败触发腐蚀爆炸（期望值）：
      <span class="hero-summary-highlight">
        每次被击败的期望真实伤害约为其最大生命的 {{ expectedExplosionOfMaxHp.toFixed(2) }}%
      </span>
    </div>

    <div v-if="coreSelected && corrosionSelected" class="hero-summary-form">
      <label class="summary-field">
        <span>污秽洗礼等级</span>
        <select v-model.number="corrosionLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field">
        <span>目标最大生命（可选）</span>
        <input v-model.number="targetMaxHp" type="number" min="0" step="100" />
      </label>
      <label class="summary-field">
        <span>被击败次数（可选）</span>
        <input v-model.number="killCount" type="number" min="0" max="50" />
      </label>
    </div>

    <div v-if="coreSelected && corrosionSelected" class="hero-summary-result">
      若目标最大生命为 {{ targetMaxHp }}，击败 {{ killCount }} 次后的期望腐蚀爆炸真实伤害：
      <span class="hero-summary-highlight">
        {{ expectedExplosionDamage.toFixed(0) }}
      </span>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：渎神（核心）与污秽洗礼。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 污秽洗礼：额外 (+5/+10/+15/+20/+25)% 腐蚀伤害；爆炸触发概率 (10/20/20/30/30)%；
// 半径内爆炸真实伤害 = 被击败目标最大生命的 125%
const CORROSION_BONUS = [5, 10, 15, 20, 25]
const EXPLOSION_CHANCE = [10, 20, 20, 30, 30] // %
const EXPLOSION_TRUE_RATIO = 1.25 // 最大生命的 125%

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('渎神'))
const corrosionSelected = computed(() => selectedSet.value.has('污秽洗礼'))

const corrosionLevel = ref<number>(3) // 污秽洗礼等级
const targetMaxHp = ref<number>(10000)
const killCount = ref<number>(1)

const corrosionDamageBonus = computed(() => {
  if (!coreSelected.value || !corrosionSelected.value) return 0
  const idx = Math.min(Math.max(corrosionLevel.value || 1, 1), 5) - 1
  return CORROSION_BONUS[idx] || 0
})

// 每次被击败的期望真实伤害 / 最大生命（百分比）
const expectedExplosionOfMaxHp = computed(() => {
  if (!coreSelected.value || !corrosionSelected.value) return 0
  const idx = Math.min(Math.max(corrosionLevel.value || 1, 1), 5) - 1
  const chance = (EXPLOSION_CHANCE[idx] || 0) / 100
  return chance * EXPLOSION_TRUE_RATIO * 100
})

const expectedExplosionDamage = computed(() => {
  if (!coreSelected.value || !corrosionSelected.value) return 0
  const each = (expectedExplosionOfMaxHp.value / 100) * Math.max(0, targetMaxHp.value || 0)
  return each * Math.max(0, killCount.value || 0)
})
</script>

