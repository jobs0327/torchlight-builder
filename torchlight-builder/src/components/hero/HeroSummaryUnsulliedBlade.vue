<template>
  <div>
    <div class="hero-summary-title">秘银净土元素伤害参考（光曜 罗莎｜无垢之刃）</div>

    <div v-if="coreSelected" class="hero-summary-line">
      期望元素伤害增幅（近似，叠加词条可计算部分）：
      <span class="hero-summary-highlight">
        约 +{{ totalElementDamageBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-line">
      分项：
      <span class="hero-summary-highlight">
        姿态额外 +{{ stanceBonusPct.toFixed(1) }}%，
        涤瑕荡秽 +{{ purityCleanBonusPct.toFixed(1) }}%，
        无疆净土 +{{ netherBonusPct.toFixed(1) }}%，
        秘银值 +{{ inkValueBonusPct.toFixed(1) }}%
      </span>
    </div>

    <div v-if="coreSelected" class="hero-summary-form">
      <label v-if="purityCleanSelected" class="summary-field">
        <span>涤瑕荡秽等级</span>
        <select v-model.number="purityCleanLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="purityCleanSelected" class="summary-field">
        <span>最大魔力（用于涤瑕荡秽）</span>
        <input v-model.number="maxMana" type="number" min="0" step="100" />
      </label>

      <label v-if="netherSelected" class="summary-field">
        <span>无疆净土等级</span>
        <select v-model.number="unboundedNetherLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="netherSelected" class="summary-field">
        <span>秘银净土内敌人数</span>
        <input v-model.number="enemyCount" type="number" min="0" max="50" step="1" />
      </label>

      <label v-if="stanceSelected" class="summary-field">
        <span>是否处于秘银姿态（未转化）</span>
        <select v-model="isInStance">
          <option :value="true">是</option>
          <option :value="false">否（处于秘银净土）</option>
        </select>
      </label>

      <label v-if="devoutSelected" class="summary-field">
        <span>竭诚奉圣等级（秘银值->元素伤害）</span>
        <select v-model.number="devoutLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="devoutSelected" class="summary-field">
        <span>当前秘银值</span>
        <input v-model.number="inkValue" type="number" min="0" max="5000" step="10" />
      </label>
    </div>

    <div v-else class="hero-summary-note" style="display: block; margin-top: 8px;">
      请先在左侧勾选：无垢之刃（核心）。
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

// 无垢无我：秘银姿态额外 +25% 元素伤害；转化为秘银净土后仍保留 40% 效果
const STANCE_ELEMENT_BONUS = 25
const STANCE_AFTER_CONVERSION_FACTOR = 0.4

// 涤瑕荡秽：每拥有 1000 点最大魔力额外 (+2/+2.5/+3/+3.5/+4)% 元素伤害，最多 (+40/+50/+60/+70/+80)%
const PURITY_PER_1000 = [2, 2.5, 3, 3.5, 4]
const PURITY_CAP = [40, 50, 60, 70, 80]

// 无疆净土：秘银净土中每存在一个敌人额外 (+6/+7/+8/+9/+10)% 元素伤害，最多额外 (+60/+70/+80/+90/+100)%
const NETHER_PER_ENEMY = [6, 7, 8, 9, 10]
const NETHER_CAP = [60, 70, 80, 90, 100]

// 竭诚奉圣：每点秘银值额外 (0.08/0.08/0.1/0.1/0.1)% 元素伤害
const INK_DAMAGE_PER_POINT = [0.08, 0.08, 0.1, 0.1, 0.1]

const purityCleanLevel = ref<number>(5)
const maxMana = ref<number>(3000)

const unboundedNetherLevel = ref<number>(5)
const enemyCount = ref<number>(5)

const isInStance = ref<boolean>(false)

const devoutLevel = ref<number>(5)
const inkValue = ref<number>(200)

const selectedSet = computed(() =>
  new Set((props.selectedTraits ?? []).map(s => (s ?? '').trim()).filter(Boolean))
)
const coreSelected = computed(() => selectedSet.value.has('无垢之刃'))
const stanceSelected = computed(() => selectedSet.value.has('无垢无我'))
const purityCleanSelected = computed(() => selectedSet.value.has('涤瑕荡秽'))
const netherSelected = computed(() => selectedSet.value.has('无疆净土'))
const devoutSelected = computed(() => selectedSet.value.has('竭诚奉圣'))

const stanceBonusPct = computed(() => {
  if (!coreSelected.value || !stanceSelected.value) return 0
  return isInStance.value ? STANCE_ELEMENT_BONUS : STANCE_ELEMENT_BONUS * STANCE_AFTER_CONVERSION_FACTOR
})

const purityCleanBonusPct = computed(() => {
  if (!coreSelected.value || !purityCleanSelected.value) return 0
  const lvIdx = Math.min(Math.max(purityCleanLevel.value || 1, 1), 5) - 1
  const per = PURITY_PER_1000[lvIdx] || 0
  const cap = PURITY_CAP[lvIdx] || 0
  const units = (Math.max(0, maxMana.value || 0) / 1000)
  const raw = units * per
  return Math.min(cap, raw)
})

const netherBonusPct = computed(() => {
  if (!coreSelected.value || !netherSelected.value) return 0
  const lvIdx = Math.min(Math.max(unboundedNetherLevel.value || 1, 1), 5) - 1
  const per = NETHER_PER_ENEMY[lvIdx] || 0
  const cap = NETHER_CAP[lvIdx] || 0
  const raw = Math.max(0, enemyCount.value || 0) * per
  return Math.min(cap, raw)
})

const inkValueBonusPct = computed(() => {
  if (!coreSelected.value || !devoutSelected.value) return 0
  const lvIdx = Math.min(Math.max(devoutLevel.value || 1, 1), 5) - 1
  const per = INK_DAMAGE_PER_POINT[lvIdx] || 0
  const v = Math.max(0, inkValue.value || 0)
  return v * per
})

const totalElementDamageBonusPct = computed(() => {
  if (!coreSelected.value) return 0
  return stanceBonusPct.value + purityCleanBonusPct.value + netherBonusPct.value + inkValueBonusPct.value
})
</script>

