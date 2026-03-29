<template>
  <div>
    <div class="hero-summary-title">冰霜脉冲与冰结效果参考（冰焰 吉玛｜冰结之心）</div>
    <div v-if="canCalc" class="hero-summary-line">
      当敌人被冰霜脉冲命中时：
      <span class="hero-summary-highlight">
        额外 +20% 冰冷伤害
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      请先在左侧勾选：冰结之心、雪上加霜。
    </div>

    <div class="hero-summary-form">
      <label v-if="snowSelected" class="summary-field">
        <span>雪上加霜等级</span>
        <select v-model.number="frostSnowLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalc">
        当前冰结效果提升：
        <span class="hero-summary-highlight">
          冰结效果约 {{ frostFreezeEffect.toFixed(1) }}%（用于提高敌人被冰结控制与冰结带来的伤害放大）
        </span>
        <span class="hero-summary-note">
          （冰结效果数值来自雪上加霜，对冰结值突破上限和冰结带来的减速/易伤有显著影响；具体伤害放大倍率以游戏实际公式为准）
        </span>
      </template>
      <div v-else class="hero-summary-note" style="display: block;">
        需要勾选上述两项后再计算。
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

// 冰焰 吉玛｜冰结之心 冰结效果
const FROST_SNOW_VALUES = [65, 90, 110, 130, 150] // 雪上加霜 冰结效果%

const frostSnowLevel = ref<number>(3)

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const coreSelected = computed(() => selectedSet.value.has('冰结之心'))
const snowSelected = computed(() => selectedSet.value.has('雪上加霜'))
const canCalc = computed(() => coreSelected.value && snowSelected.value)

const frostFreezeEffect = computed(
  () => (canCalc.value ? FROST_SNOW_VALUES[Math.min(Math.max(frostSnowLevel.value || 1, 1), 5) - 1] || 0 : 0)
)
</script>

