<template>
  <div class="anger-summary">
    <div class="hero-summary-title">爆裂与怒气数值（狂人 雷恩｜怒火）</div>
    <p class="anger-summary-intro">
      爆裂技能数值来自 <code>heroes.json</code> 的 <code>burstSkill</code>（与游戏内「爆裂」面板一致）；特性增伤与尽情挥发模型仍为简化估算。
    </p>

    <!-- 游戏内爆裂面板（数据源） -->
    <div class="anger-block anger-block--panel">
      <div class="anger-block-title">爆裂 · 游戏面板数据（heroes.json）</div>
      <table class="anger-table">
        <tbody>
          <tr>
            <td>技能名称</td>
            <td class="anger-num">{{ burstResolved.skillName }}</td>
          </tr>
          <tr>
            <td>范围</td>
            <td class="anger-num">{{ burstResolved.radiusMeters }} 米内范围爆炸</td>
          </tr>
          <tr>
            <td>伤害</td>
            <td class="anger-num">
              相当于 <strong>{{ burstResolved.weaponDamageMultiplierPct }}%</strong> 武器伤害
            </td>
          </tr>
          <tr>
            <td>技能等级成长</td>
            <td class="anger-num">
              每 +1 等级 <strong>×{{ burstResolved.perSkillLevelMoreMultiplicative }}</strong>（叠乘，共 {{ burstSkillLevel }} 级 → ×{{
                burstLevelMoreStack.toFixed(4)
              }}）
            </td>
          </tr>
          <tr>
            <td>基础冷却（触发间隔下限）</td>
            <td class="anger-num">{{ burstResolved.baseCooldownSec.toFixed(2) }} 秒</td>
          </tr>
          <tr v-if="burstResolved.tags.length">
            <td>技能标签</td>
            <td class="anger-num">{{ burstResolved.tags.join('、') }}</td>
          </tr>
        </tbody>
      </table>
      <ul v-if="burstResolved.notes.length" class="anger-burst-notes">
        <li v-for="(n, i) in burstResolved.notes" :key="i">{{ n }}</li>
      </ul>
    </div>

    <div class="hero-summary-form">
      <label class="summary-field">
        <span>怒气上限（用于估算）</span>
        <input v-model.number="rageMax" type="number" min="0" />
      </label>
      <label v-if="furySelected" class="summary-field">
        <span>爆裂技能等级（叠乘）</span>
        <input v-model.number="burstSkillLevel" type="number" min="1" max="99" step="1" />
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
      <label v-if="nukebSelected" class="summary-field">
        <span>怒不可遏等级</span>
        <select v-model.number="nukebLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="jingqingSelected" class="summary-field">
        <span>尽情挥发等级</span>
        <select v-model.number="jingqingLevel">
          <option v-for="n in 5" :key="n" :value="n">{{ n }}</option>
        </select>
      </label>
      <label v-if="jingqingSelected" class="summary-field">
        <span>基础攻击速度倍率</span>
        <input v-model.number="attackSpeedMult" type="number" min="0.5" max="5" step="0.05" />
      </label>
      <span v-if="jingqingSelected" class="anger-field-hint">
        默认 1.5；等效攻速相关加成 = (倍率 − 1) × 100%，再按尽情挥发档位作用于爆裂冷却回复（可与面板「攻击速度提高」等合并为倍率后填入）
      </span>
    </div>

    <!-- 爆裂冷却 -->
    <div v-if="furySelected" class="anger-block">
      <div class="anger-block-title">爆裂冷却时间</div>
      <table class="anger-table">
        <tbody>
          <tr>
            <td>基础冷却（与 burstSkill / 怒火文案一致）</td>
            <td class="anger-num">{{ burstResolved.baseCooldownSec.toFixed(3) }} 秒</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>等效攻击速度相关加成（由倍率换算）</td>
            <td class="anger-num">+{{ attackSpeedRelatedBonusPct.toFixed(1) }}%（倍率 {{ attackSpeedMultSafe.toFixed(2) }}）</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>尽情挥发 · 作用于冷却回复的系数</td>
            <td class="anger-num">{{ jingqingApplyPct }}%</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>冷却回复速度倍率（模型）</td>
            <td class="anger-num">× {{ burstCdRecoveryMult.toFixed(4) }}</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>爆裂冷却回复速度提高（相对未转化前）</td>
            <td class="anger-num highlight">+{{ burstCdRecoverySpeedIncreasePct.toFixed(2) }}%</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>估算爆裂触发频率提高（与回复速度一致）</td>
            <td class="anger-num">+{{ burstCdRecoverySpeedIncreasePct.toFixed(2) }}%</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>估算每秒爆裂次数（仅冷却模型）</td>
            <td class="anger-num">≈ {{ burstPerSecondEstimate.toFixed(2) }} 次/秒</td>
          </tr>
          <tr v-if="jingqingSelected">
            <td>有效爆裂间隔（估算）</td>
            <td class="anger-num highlight">≈ {{ burstEffectiveIntervalSec.toFixed(4) }} 秒</td>
          </tr>
          <tr v-else>
            <td>有效爆裂间隔（未点尽情挥发）</td>
            <td class="anger-num highlight">= {{ burstResolved.baseCooldownSec.toFixed(3) }} 秒</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 怒气 → 暴击值（怒不可遏） -->
    <div v-if="nukebSelected" class="anger-block">
      <div class="anger-block-title">怒气值 → 暴击值（怒不可遏）</div>
      <table class="anger-table">
        <tbody>
          <tr>
            <td>每 1 点怒气暴击值（当前档位）</td>
            <td class="anger-num">{{ nukebCritPerRagePoint }}%</td>
          </tr>
          <tr>
            <td>满怒气（{{ rageMaxSafe }}）时暴击值加成（线性相加）</td>
            <td class="anger-num highlight">≈ {{ critValuePctAtRage.toFixed(1) }}%</td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 爆裂伤害拆分：仅选核心「怒火」即可见怒气通用 + 怒火等级爆裂增伤 -->
    <div v-if="canShowBurstDamage" class="anger-block">
      <div class="anger-block-title">爆裂伤害与怒气增伤（%）</div>
      <table class="anger-table">
        <tbody>
          <tr>
            <td>怒气通用 · 每点怒气伤害（非爆裂专属）</td>
            <td class="anger-num">+{{ rageGeneralPct.toFixed(1) }}%</td>
          </tr>
          <tr>
            <td>怒火 · 每级额外爆裂伤害</td>
            <td class="anger-num">+{{ furyFromLevelsPct.toFixed(1) }}%（{{ talentLevel }} 级 × 2.9%）</td>
          </tr>
          <tr>
            <td>顾此失彼 · 额外爆裂伤害</td>
            <td class="anger-num">
              <template v-if="guciSelected">+{{ guciPct }}%</template>
              <span v-else class="anger-muted">— 未勾选（计 0%）</span>
            </td>
          </tr>
          <tr>
            <td>暴怒原罪 · 范围叠满额外爆裂伤害</td>
            <td class="anger-num">
              <template v-if="yuanzuiSelected">+{{ yuanzuiPct }}%</template>
              <span v-else class="anger-muted">— 未勾选（计 0%）</span>
            </td>
          </tr>
          <tr class="anger-row-total">
            <td><strong>额外爆裂伤害合计</strong>（不含怒气通用 0.22%/点）</td>
            <td class="anger-num highlight">
              <strong>+{{ extraBurstPct.toFixed(1) }}%</strong>
            </td>
          </tr>
          <tr class="anger-row-total">
            <td><strong>总增伤合计</strong>（怒气通用 + 上述爆裂相关）</td>
            <td class="anger-num highlight">
              <strong>+{{ currentTotalBonus.toFixed(1) }}%</strong>
              （约 {{ totalDamageMult.toFixed(2) }} 倍）
            </td>
          </tr>
          <template v-if="jingqingSelected">
            <tr class="anger-row-jingqing">
              <td colspan="2" class="anger-subhead">尽情挥发 · 纳入统计（与上表伤害独立，为冷却/频率）</td>
            </tr>
            <tr>
              <td>基础攻击速度倍率 → 等效攻速加成</td>
              <td class="anger-num">{{ attackSpeedMultSafe.toFixed(2) }} → +{{ attackSpeedRelatedBonusPct.toFixed(1) }}%</td>
            </tr>
            <tr>
              <td>爆裂冷却回复速度提高</td>
              <td class="anger-num highlight">+{{ burstCdRecoverySpeedIncreasePct.toFixed(2) }}%</td>
            </tr>
            <tr>
              <td>有效爆裂间隔 / 每秒爆裂次数（估算）</td>
              <td class="anger-num">
                {{ burstEffectiveIntervalSec.toFixed(4) }} 秒 · ≈ {{ burstPerSecondEstimate.toFixed(2) }} 次/秒
              </td>
            </tr>
          </template>
        </tbody>
      </table>
      <p v-if="!guciSelected || !yuanzuiSelected" class="anger-partial-hint">
        未勾选的特性在表中按 0% 计入；勾选「顾此失彼」「暴怒原罪」后可填入对应等级。
      </p>
    </div>

    <!-- 武器伤害归一 = 1：技能倍率 × 等级叠乘 × 特性增伤 × 冷却 -->
    <div v-if="canShowBurstDamage" class="anger-block">
      <div class="anger-block-title">爆裂输出估算（武器伤害 = 1，后续在数据计算模块会根据武器实际点伤和技能等级计算具体数值）</div>
      <table class="anger-table">
        <tbody>
          <tr>
            <td>武器伤害（归一）</td>
            <td class="anger-num">{{ WEAPON_REF }}</td>
          </tr>
          <tr>
            <td>技能部分（{{ burstResolved.weaponDamageMultiplierPct }}% × 等级叠乘）</td>
            <td class="anger-num">× {{ burstWeaponPartMult.toFixed(4) }}</td>
          </tr>
          <tr>
            <td>特性总增伤倍率</td>
            <td class="anger-num">× {{ totalDamageMult.toFixed(4) }}</td>
          </tr>
          <tr>
            <td>单次爆裂期望（相对武器 1）</td>
            <td class="anger-num">
              <strong>{{ burstDamagePerHitRef.toFixed(4) }}</strong>
            </td>
          </tr>
          <tr>
            <td>每秒爆裂次数（1 ÷ 有效间隔）</td>
            <td class="anger-num">≈ {{ burstPerSecondEstimate.toFixed(4) }} 次/秒</td>
          </tr>
          <tr class="anger-row-total">
            <td><strong>爆裂 DPS</strong>（单次 × 频率，仅冷却上限）</td>
            <td class="anger-num highlight">
              <strong>{{ burstDpsCooldownLimitedRef.toFixed(4) }}</strong>
            </td>
          </tr>
        </tbody>
      </table>
      <p class="anger-final-hint">
        公式：<code>武器1 × ({{ burstResolved.weaponDamageMultiplierPct }}%÷100) × {{ burstResolved.perSkillLevelMoreMultiplicative }}^(等级−1) × (1+总增伤%÷100) ×
        每秒触发次数</code>。双持时游戏内武器基数为两把平均；此处仅归一。不含点伤词缀、暴击、命中上限与义愤填膺等。
      </p>
    </div>

    <div v-else class="hero-summary-note anger-missing">
      请先勾选核心特性「怒火」，以查看怒气与爆裂相关增伤数值。
    </div>

    <div class="hero-summary-result" v-if="canShowBurstDamage">
      <span class="hero-summary-note">
        暴怒原罪按「技能范围叠满」上限计算；不计暴击率、攻速命中次数与义愤填膺等其它分支。
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
// eslint-disable-next-line @typescript-eslint/ban-ts-comment
// @ts-ignore
import heroesJson from '@/data/heroes/heroes.json'
import {
  DEFAULT_ANGER_ATTACK_SPEED_MULT,
  NUKEB_CRIT_PCT_PER_RAGE_POINT,
  JINGQING_AS_TO_BURST_CD_PCT,
  GUCI_EXTRA_BURST_PCT,
  YUANZUI_EXTRA_BURST_CAP_PCT,
  rageGeneralDamagePct,
  furyTraitBurstFromLevels,
  critValuePctFromRageAtLevel,
  effectiveBurstIntervalSec as computeBurstCooldownModel,
  attackSpeedRelatedBonusPctFromMult,
  burstCooldownRecoverySpeedIncreasePct,
  clampTraitLevel
} from '@/utils/heroAngerBurst'
import {
  burstSkillWeaponPartMultiplier,
  getAngerHeroFromList,
  resolveAngerBurstSkill
} from '@/utils/angerHeroBurstConfig'

interface Props {
  selectedTraits?: string[]
}

const props = defineProps<Props>()

const angerHeroJson = computed(() => getAngerHeroFromList(heroesJson as unknown[]))
const burstResolved = computed(() => resolveAngerBurstSkill(angerHeroJson.value))

const burstSkillLevel = ref<number>(1)
const burstSkillLevelSafe = computed(() =>
  Math.min(99, Math.max(1, Math.floor(Number(burstSkillLevel.value) || 1)))
)

const burstLevelMoreStack = computed(() =>
  Math.pow(burstResolved.value.perSkillLevelMoreMultiplicative, burstSkillLevelSafe.value - 1)
)

const burstWeaponPartMult = computed(() =>
  burstSkillWeaponPartMultiplier(
    burstResolved.value.weaponDamageMultiplierPct,
    burstSkillLevelSafe.value,
    burstResolved.value.perSkillLevelMoreMultiplicative
  )
)

/** 武器伤害归一，与面板「340% 武器伤害」相乘得到期望击中 */
const WEAPON_REF = 1

const selectedSet = computed(() => new Set(props.selectedTraits ?? []))
const furySelected = computed(() => selectedSet.value.has('怒火'))
const guciSelected = computed(() => selectedSet.value.has('顾此失彼'))
const yuanzuiSelected = computed(() => selectedSet.value.has('暴怒原罪'))
const nukebSelected = computed(() => selectedSet.value.has('怒不可遏'))
const jingqingSelected = computed(() => selectedSet.value.has('尽情挥发'))
/** 仅核心「怒火」即可展示怒气与爆裂增伤；顾此失彼/暴怒原罪未选时按 0% 计 */
const canShowBurstDamage = computed(() => furySelected.value)

const rageMax = ref<number>(100)
const talentLevel = ref<number>(3)
const guciLevel = ref<number>(3)
const yuanzuiLevel = ref<number>(3)
const nukebLevel = ref<number>(3)
const jingqingLevel = ref<number>(3)
/** 基础攻击速度倍率，默认 1.5 → 等效 +50% 攻速相关加成 */
const attackSpeedMult = ref<number>(DEFAULT_ANGER_ATTACK_SPEED_MULT)

const rageMaxSafe = computed(() => Math.max(0, Number(rageMax.value) || 0))

const nukebCritPerRagePoint = computed(() => {
  const lv = clampTraitLevel(nukebLevel.value)
  return NUKEB_CRIT_PCT_PER_RAGE_POINT[lv - 1]!
})

const critValuePctAtRage = computed(() =>
  nukebSelected.value ? critValuePctFromRageAtLevel(rageMaxSafe.value, nukebLevel.value) : 0
)

const jingqingApplyPct = computed(() => {
  const lv = clampTraitLevel(jingqingLevel.value)
  return JINGQING_AS_TO_BURST_CD_PCT[lv - 1]!
})

const attackSpeedMultSafe = computed(() => {
  const m = Number(attackSpeedMult.value)
  return Number.isFinite(m) && m > 0 ? m : DEFAULT_ANGER_ATTACK_SPEED_MULT
})

const attackSpeedRelatedBonusPct = computed(() =>
  attackSpeedRelatedBonusPctFromMult(attackSpeedMultSafe.value)
)

const burstCdRecoveryMult = computed(() => {
  if (!jingqingSelected.value) return 1
  return computeBurstCooldownModel(
    attackSpeedRelatedBonusPct.value,
    jingqingLevel.value,
    burstResolved.value.baseCooldownSec
  ).recoveryMult
})

const burstEffectiveIntervalSec = computed(() => {
  const base = burstResolved.value.baseCooldownSec
  if (!jingqingSelected.value) return base
  return computeBurstCooldownModel(
    attackSpeedRelatedBonusPct.value,
    jingqingLevel.value,
    base
  ).intervalSec
})

const burstCdRecoverySpeedIncreasePct = computed(() =>
  jingqingSelected.value ? burstCooldownRecoverySpeedIncreasePct(burstCdRecoveryMult.value) : 0
)

/** 仅按有效间隔估算，不计施法/命中门槛 */
const burstPerSecondEstimate = computed(() => {
  const t = burstEffectiveIntervalSec.value
  return t > 0 ? 1 / t : 0
})

const rageGeneralPct = computed(() => rageGeneralDamagePct(rageMaxSafe.value))
const furyFromLevelsPct = computed(() => furyTraitBurstFromLevels(talentLevel.value))

const guciPct = computed(() => GUCI_EXTRA_BURST_PCT[clampTraitLevel(guciLevel.value) - 1]!)
const yuanzuiPct = computed(() => YUANZUI_EXTRA_BURST_CAP_PCT[clampTraitLevel(yuanzuiLevel.value) - 1]!)

const extraBurstPct = computed(() => {
  if (!furySelected.value) return 0
  let x = furyTraitBurstFromLevels(talentLevel.value)
  if (guciSelected.value) {
    x += GUCI_EXTRA_BURST_PCT[clampTraitLevel(guciLevel.value) - 1]!
  }
  if (yuanzuiSelected.value) {
    x += YUANZUI_EXTRA_BURST_CAP_PCT[clampTraitLevel(yuanzuiLevel.value) - 1]!
  }
  return x
})

const currentTotalBonus = computed(() => {
  if (!furySelected.value) return 0
  return rageGeneralDamagePct(rageMaxSafe.value) + extraBurstPct.value
})

const totalDamageMult = computed(() => 1 + currentTotalBonus.value / 100)

/** 单次爆裂期望：武器1 × 技能倍率×等级叠乘 × 特性增伤 */
const burstDamagePerHitRef = computed(() => {
  if (!furySelected.value) return 0
  return WEAPON_REF * burstWeaponPartMult.value * totalDamageMult.value
})

/** 爆裂 DPS：仅冷却限制（无「每秒最多触发次数」以外的命中瓶颈） */
const burstDpsCooldownLimitedRef = computed(() => {
  if (!furySelected.value) return 0
  return burstDamagePerHitRef.value * burstPerSecondEstimate.value
})
</script>

<style scoped>
.anger-summary {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.78);
}

.anger-summary-intro {
  margin: 0 0 10px;
  font-size: 11px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.5);
}

.anger-summary-intro code {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(200, 220, 255, 0.95);
}

.anger-block--panel {
  border-color: rgba(100, 160, 255, 0.2);
}

.anger-burst-notes {
  margin: 8px 0 0;
  padding-left: 18px;
  font-size: 10px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.48);
}

.anger-field-hint {
  flex-basis: 100%;
  font-size: 10px;
  color: rgba(255, 255, 255, 0.42);
  margin-top: -4px;
}

.anger-block {
  margin: 12px 0;
  padding: 10px 10px 8px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.anger-block-title {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 230, 200, 0.95);
  margin-bottom: 8px;
}

.anger-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}

.anger-table td {
  padding: 5px 8px 5px 0;
  vertical-align: top;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  color: rgba(220, 230, 255, 0.88);
}

.anger-table tr:last-child td {
  border-bottom: none;
}

.anger-num {
  text-align: right;
  white-space: nowrap;
  font-variant-numeric: tabular-nums;
  color: #a5d4ff;
}

.anger-num.highlight {
  color: #ffcc66;
  font-weight: 600;
}

.anger-row-total td {
  padding-top: 8px;
}

.anger-full-ref {
  margin-top: 8px;
}

.anger-missing {
  margin-top: 8px;
}

.anger-muted {
  color: rgba(255, 255, 255, 0.38);
  font-style: italic;
}

.anger-partial-hint {
  margin: 8px 0 0;
  font-size: 10px;
  line-height: 1.4;
  color: rgba(255, 255, 255, 0.45);
}

.anger-row-jingqing td {
  padding-top: 10px;
  border-bottom: none;
}

.anger-subhead {
  font-size: 11px;
  font-weight: 600;
  color: rgba(230, 210, 255, 0.9);
}

.anger-final-hint {
  margin: 8px 0 0;
  font-size: 10px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.45);
}

.anger-final-hint code {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(200, 220, 255, 0.95);
}
</style>
