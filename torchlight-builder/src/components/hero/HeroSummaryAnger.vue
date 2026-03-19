<template>
  <div>
    <div class="hero-summary-title">爆裂增伤参考（狂人 雷恩｜怒火）</div>
    <div v-if="canCalc" class="hero-summary-line">
      满配参考（怒气上限 100，怒火 5 级，顾此失彼 5 级，暴怒原罪 5 级）：
      <span class="hero-summary-highlight">
        约 {{ fullBuildTotalBonus.toFixed(1) }}% 爆裂伤害（约 {{ (1 + fullBuildTotalBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：怒火、顾此失彼、暴怒原罪。
    </div>
    <div class="hero-summary-form">
      <label class="summary-field">
        <span>怒气上限</span>
        <input v-model.number="rageMax" type="number" min="0" />
      </label>
      <label v-if="furySelected" class="summary-field">
        <span>怒火等级</span>
        <select v-model.number="talentLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="guciSelected" class="summary-field">
        <span>顾此失彼等级</span>
        <select v-model.number="guciLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="yuanzuiSelected" class="summary-field">
        <span>暴怒原罪等级</span>
        <select v-model.number="yuanzuiLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>
    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ currentTotalBonus.toFixed(1) }}% 爆裂伤害（约 {{ (1 + currentTotalBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （假设暴怒原罪均吃满技能范围上限，不计暴击与攻速频率提升）
        </span>
      </template>
      <div v-else class="hero-summary-note">
        需要勾选上述三个分支后再计算。
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

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const furySelected = computed(() => selectedSet.value.has('怒火'))
const guciSelected = computed(() => selectedSet.value.has('顾此失彼'))
const yuanzuiSelected = computed(() => selectedSet.value.has('暴怒原罪'))
const canCalc = computed(() => furySelected.value && guciSelected.value && yuanzuiSelected.value)

// 狂人 雷恩｜怒火 爆裂增伤计算表单
const rageMax = ref<number>(100)
const talentLevel = ref<number>(5) // 怒火等级
const guciLevel = ref<number>(5) // 顾此失彼
const yuanzuiLevel = ref<number>(5) // 暴怒原罪

const GUCI_VALUES = [66, 77, 88, 99, 110]
const YUANZUI_VALUES = [40, 51, 63, 76, 90]

function calcTotalBonus(rage: number, talentLv: number, guLv: number, yzLv: number): number {
  const dmgFromRage = rage * 0.22 // 每点怒气 0.22% 伤害
  const explodeFromTalent = talentLv * 2.9 // 每级 2.9% 爆裂伤
  const guci = GUCI_VALUES[Math.min(Math.max(guLv, 1), 5) - 1] || 0
  const yuanzui = YUANZUI_VALUES[Math.min(Math.max(yzLv, 1), 5) - 1] || 0
  return dmgFromRage + explodeFromTalent + guci + yuanzui
}

const fullBuildTotalBonus = computed(() => (canCalc.value ? calcTotalBonus(100, 5, 5, 5) : 0))
const currentTotalBonus = computed(() => {
  if (!canCalc.value) return 0
  return calcTotalBonus(
    Math.max(0, rageMax.value || 0),
    talentLevel.value || 1,
    guciLevel.value || 1,
    yuanzuiLevel.value || 1
  )
})
</script>

