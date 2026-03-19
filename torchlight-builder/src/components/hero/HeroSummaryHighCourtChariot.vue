<template>
  <div>
    <div class="hero-summary-title">圣光领域伤害参考（光曜 罗莎｜圣庭战车）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      圣光领域内额外伤害增幅（近似）：
      <span class="hero-summary-highlight">
        约 +{{ totalSacredFieldBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      其中：
      <span class="hero-summary-highlight">
        基础 +20% ，以一敌百约 +{{ perEnemyBonusPct.toFixed(1) }}%，天降神兵约 +{{ fortitudeBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="manyEnemiesSelected" class="summary-field">
        <span>以一敌百等级</span>
        <select v-model.number="manyEnemiesTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field">
        <span>圣光领域内敌人数</span>
        <input v-model.number="enemyCount" type="number" min="0" max="50" step="1" />
      </label>

      <label v-if="dropSoldierSelected" class="summary-field">
        <span>天降神兵等级</span>
        <select v-model.number="dropSoldierTraitLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field">
        <span>当前斗志点数</span>
        <input v-model.number="fortitude" type="number" min="0" max="200" step="1" />
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：圣庭战车（核心）。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 圣庭战车：在圣光领域中时，额外 +20% 伤害
const BASE_SACRED_DAMAGE = 20

// 以一敌百：每存在一个敌人，额外 (+7/+8/+9/9.5/+10)% 伤害，最多额外 +100%
const MANY_ENEMIES_PER = [7, 8, 9, 9.5, 10]
const MANY_ENEMIES_CAP = 100

// 天降神兵：当前每有 1 点斗志， 对圣光领域中的敌人额外 (0.3/0.37/0.44/0.51/0.58)% 伤害
const FORTITUDE_DAMAGE_PER = [0.3, 0.37, 0.44, 0.51, 0.58]

const manyEnemiesTraitLevel = ref<number>(5)
const enemyCount = ref<number>(10)

const dropSoldierTraitLevel = ref<number>(5)
const fortitude = ref<number>(15)

const selectedSet = computed(() =>
  new Set((props.selectedTraits ?? []).map(s => (s ?? '').trim()).filter(Boolean))
)
const coreSelected = computed(() => selectedSet.value.has('圣庭战车'))
const manyEnemiesSelected = computed(() => selectedSet.value.has('以一敌百'))
const dropSoldierSelected = computed(() => selectedSet.value.has('天降神兵'))

const perEnemyBonusPct = computed(() => {
  if (!coreSelected.value || !manyEnemiesSelected.value) return 0
  const lvIdx = Math.min(Math.max(manyEnemiesTraitLevel.value || 1, 1), 5) - 1
  const per = MANY_ENEMIES_PER[lvIdx] || 0
  return Math.min(MANY_ENEMIES_CAP, Math.max(0, enemyCount.value || 0) * per)
})

const fortitudeBonusPct = computed(() => {
  if (!coreSelected.value || !dropSoldierSelected.value) return 0
  const lvIdx = Math.min(Math.max(dropSoldierTraitLevel.value || 1, 1), 5) - 1
  const per = FORTITUDE_DAMAGE_PER[lvIdx] || 0
  return Math.max(0, fortitude.value || 0) * per
})

const totalSacredFieldBonusPct = computed(() => {
  if (!coreSelected.value) return 0
  return BASE_SACRED_DAMAGE + perEnemyBonusPct.value + fortitudeBonusPct.value
})
</script>

