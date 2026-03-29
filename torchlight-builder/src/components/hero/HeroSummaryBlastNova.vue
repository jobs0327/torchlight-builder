<template>
  <div>
    <div class="hero-summary-title">炸弹伤害参考（逃脱者 宾｜爆破新星）</div>
    <div v-if="canCalcFull" class="hero-summary-line">
      满配参考（攻速 +100%，施法速度 +100%，火力覆盖 5 级，爆风弹袭 5 级，虚实投递 5 级，辐射效应 5 级，狂暴猎犬 5 级，场上存在 10 枚炸弹）：
      <span class="hero-summary-highlight">
        约 {{ blastFullBonus.toFixed(1) }}% 炸弹伤害（约 {{ (1 + blastFullBonus / 100).toFixed(2) }} 倍）
      </span>
    </div>
    <div v-else class="hero-summary-note" style="display: block; margin: 8px 0 0;">
      勾选“爆破新星”后下方会开始计算；若要看满配参考，需要再勾选火力覆盖/爆风弹袭/辐射效应/狂暴猎犬。
    </div>

    <div class="hero-summary-form">
      <label class="summary-field">
        <span>额外攻击速度%</span>
        <input v-model.number="blastAttackSpeedPct" type="number" min="0" max="300" />
      </label>
      <label class="summary-field">
        <span>额外施法速度%</span>
        <input v-model.number="blastCastSpeedPct" type="number" min="0" max="300" />
      </label>
      <label v-if="coverSelected" class="summary-field">
        <span>火力覆盖等级</span>
        <select v-model.number="blastCoverLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="stormSelected" class="summary-field">
        <span>爆风弹袭等级</span>
        <select v-model.number="blastStormLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="fakeSelected" class="summary-field">
        <span>虚实投递等级</span>
        <select v-model.number="blastFakeLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="radSelected" class="summary-field">
        <span>辐射效应等级</span>
        <select v-model.number="blastRadiationLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="dogSelected" class="summary-field">
        <span>狂暴猎犬等级</span>
        <select v-model.number="blastDogLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label class="summary-field">
        <span>场上炸弹数量</span>
        <input v-model.number="blastBombCount" type="number" min="1" max="10" />
      </label>
      <label class="summary-field">
        <span>是否视为近距引爆</span>
        <select v-model="blastNear">
          <option :value="true">是</option>
          <option :value="false">否</option>
        </select>
      </label>
    </div>

    <div class="hero-summary-result">
      <template v-if="canCalcCurrent">
        当前配置下：
        <span class="hero-summary-highlight">
          约 {{ blastCurrentBonus.toFixed(1) }}% 炸弹伤害（约 {{ (1 + blastCurrentBonus / 100).toFixed(2) }} 倍）
        </span>
        <span class="hero-summary-note">
          （包含爆破新星核心 30% 炸弹伤害、攻速/施法速度折算的炸弹伤害、已选分支的炸弹伤害加成）
        </span>
      </template>
      <div v-else class="hero-summary-note">
        请先在左侧勾选：爆破新星。
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
const coreSelected = computed(() => selectedSet.value.has('爆破新星'))
const coverSelected = computed(() => selectedSet.value.has('火力覆盖'))
const stormSelected = computed(() => selectedSet.value.has('爆风弹袭'))
const fakeSelected = computed(() => selectedSet.value.has('虚实投递'))
const radSelected = computed(() => selectedSet.value.has('辐射效应'))
const dogSelected = computed(() => selectedSet.value.has('狂暴猎犬'))
const canCalcFull = computed(() => coreSelected.value && coverSelected.value && stormSelected.value && radSelected.value && dogSelected.value)
const canCalcCurrent = computed(() => coreSelected.value)

// 逃脱者 宾｜爆破新星 炸弹伤害
const BLAST_CORE_BOMB = 30 // 爆破新星额外 +30% 炸弹伤害
const BLAST_COVER_VALUES = [10, 14, 18, 22, 26] // 火力覆盖 炸弹伤害
const BLAST_STORM_VALUES = [22, 28, 34, 41, 48] // 爆风弹袭 周围无敌人时 炸弹伤害
const BLAST_RAD_PER = [0.35, 0.42, 0.48, 0.53, 0.6] // 辐射效应 每 1% 投射物速度 近距伤害
const BLAST_RAD_CAP = [35, 42, 48, 53, 60] // 辐射效应 上限
const BLAST_DOG_PER = [4, 4.8, 5.5, 6.3, 7] // 狂暴猎犬 每颗炸弹

const blastAttackSpeedPct = ref<number>(100)
const blastCastSpeedPct = ref<number>(100)
const blastCoverLevel = ref<number>(3)
const blastStormLevel = ref<number>(3)
const blastFakeLevel = ref<number>(3)
const blastRadiationLevel = ref<number>(3)
const blastDogLevel = ref<number>(3)
const blastBombCount = ref<number>(10)
const blastNear = ref<boolean>(true)

function calcBlastBonus(
  atkSpd: number,
  castSpd: number,
  coverLv: number,
  stormLv: number,
  radiationLv: number,
  dogLv: number,
  bombCount: number,
  near: boolean,
  hasCore: boolean,
  hasCover: boolean,
  hasStorm: boolean,
  hasRadiation: boolean,
  hasDog: boolean
): number {
  const core = hasCore ? BLAST_CORE_BOMB : 0
  const atk = Math.max(0, atkSpd || 0)
  const cast = Math.max(0, castSpd || 0)
  // 每 +1% 攻速 / 施法速度，对对应炸弹伤害 +1%
  const bombFromSpeed = atk + cast
  const cover = hasCover ? BLAST_COVER_VALUES[Math.min(Math.max(coverLv, 1), 5) - 1] || 0 : 0
  const storm = hasStorm ? BLAST_STORM_VALUES[Math.min(Math.max(stormLv, 1), 5) - 1] || 0 : 0
  const radPer = hasRadiation ? BLAST_RAD_PER[Math.min(Math.max(radiationLv, 1), 5) - 1] || 0 : 0
  const radCap = hasRadiation ? BLAST_RAD_CAP[Math.min(Math.max(radiationLv, 1), 5) - 1] || 0 : 0
  const projSpeed = near ? 20 : 0 // 简化：若视为近距且有高投射物速度，则用 20% 作为示例
  const radRaw = projSpeed * radPer
  const rad = Math.min(radRaw, radCap)
  const bombs = Math.min(Math.max(bombCount || 1, 1), 10)
  const dogPer = hasDog ? BLAST_DOG_PER[Math.min(Math.max(dogLv, 1), 5) - 1] || 0 : 0
  const dog = bombs * dogPer
  return core + bombFromSpeed + cover + storm + rad + dog
}

const blastFullBonus = computed(() => {
  if (!canCalcFull.value) return 0
  return calcBlastBonus(100, 100, 5, 5, 5, 5, 10, true, true, true, true, true, true)
})

const blastCurrentBonus = computed(() => {
  if (!canCalcCurrent.value) return 0
  return calcBlastBonus(
    blastAttackSpeedPct.value || 0,
    blastCastSpeedPct.value || 0,
    blastCoverLevel.value || 1,
    blastStormLevel.value || 1,
    blastRadiationLevel.value || 1,
    blastDogLevel.value || 1,
    blastBombCount.value || 1,
    blastNear.value,
    coreSelected.value,
    coverSelected.value,
    stormSelected.value,
    radSelected.value,
    dogSelected.value
  )
})
</script>

