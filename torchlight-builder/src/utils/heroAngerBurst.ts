/**
 * 狂人 雷恩｜怒火 — 爆裂 / 怒气 / 暴击值 数值整理（与 heroes.json 文案一致，演示用）
 */

export const BURST_BASE_CD_SEC = 0.3

/** 演示用：基础攻击速度倍率 1.5（相对 1.0）→ 等效攻速相关加成 +50% */
export const DEFAULT_ANGER_ATTACK_SPEED_MULT = 1.5

/** 由攻击速度倍率换算为「攻击速度相关加成总和（%）」： (倍率 − 1) × 100，下限 0 */
export function attackSpeedRelatedBonusPctFromMult(attackSpeedMult: number): number {
  const m = typeof attackSpeedMult === 'number' && Number.isFinite(attackSpeedMult) ? attackSpeedMult : 1
  return Math.max(0, m - 1) * 100
}

/** 尽情挥发模型下：爆裂冷却回复速度相对基础（×1）的提高幅度（%），与估算触发频率倍率一致 */
export function burstCooldownRecoverySpeedIncreasePct(recoveryMult: number): number {
  return (Math.max(recoveryMult, 1e-9) - 1) * 100
}

/** 怒不可遏：每 1 点怒气提供的暴击值（%），档位 1–5 */
export const NUKEB_CRIT_PCT_PER_RAGE_POINT = [0.3, 0.5, 0.7, 0.9, 1.1] as const

/** 尽情挥发：攻击速度相关加成作用于爆裂冷却回复的系数（%），档位 1–5 */
export const JINGQING_AS_TO_BURST_CD_PCT = [70, 80, 90, 100, 110] as const

/** 顾此失彼：额外爆裂伤害（%） */
export const GUCI_EXTRA_BURST_PCT = [66, 77, 88, 99, 110] as const

/** 暴怒原罪：技能范围叠满时额外爆裂伤害（%） */
export const YUANZUI_EXTRA_BURST_CAP_PCT = [40, 51, 63, 76, 90] as const

/** 怒火核心：每 1 点怒气额外伤害（%） */
export const RAGE_PER_POINT_DAMAGE_PCT = 0.22

/** 怒火核心：每级「怒火」额外爆裂伤害（%） */
export const FURY_TRAIT_BURST_PER_LEVEL_PCT = 2.9

export function clampTraitLevel(n: unknown): number {
  const x = typeof n === 'number' && Number.isFinite(n) ? Math.floor(n) : 1
  return Math.min(Math.max(x, 1), 5)
}

/** 怒气通用伤害加成（%）：每点怒气 0.22% */
export function rageGeneralDamagePct(rage: number): number {
  return Math.max(0, rage) * RAGE_PER_POINT_DAMAGE_PCT
}

/** 怒火特性：来自等级的爆裂伤害（%） */
export function furyTraitBurstFromLevels(talentLv: number): number {
  return clampTraitLevel(talentLv) * FURY_TRAIT_BURST_PER_LEVEL_PCT
}

/** 额外爆裂伤害（%）：怒火等级 + 顾此失彼 + 暴怒原罪（不含怒气通用 0.22%） */
export function extraBurstDamagePct(talentLv: number, guLv: number, yzLv: number): number {
  const g = clampTraitLevel(guLv)
  const y = clampTraitLevel(yzLv)
  return (
    furyTraitBurstFromLevels(talentLv) +
    GUCI_EXTRA_BURST_PCT[g - 1]! +
    YUANZUI_EXTRA_BURST_CAP_PCT[y - 1]!
  )
}

/** 与旧版 HeroSummaryAnger 一致的总增伤（%）：怒气通用 + 额外爆裂 */
export function totalAngerDamageBonusPct(
  rage: number,
  talentLv: number,
  guLv: number,
  yzLv: number
): number {
  return rageGeneralDamagePct(rage) + extraBurstDamagePct(talentLv, guLv, yzLv)
}

/**
 * 怒不可遏：满怒气时暴击值相关加成（%）
 * 文案「每拥有 1 点怒气，(0.3/…/1.1)% 暴击值」→ 线性相加：怒气 × 每点 %
 */
export function critValuePctFromRageAtLevel(rage: number, nukebLv: number): number {
  const lv = clampTraitLevel(nukebLv)
  const perPoint = NUKEB_CRIT_PCT_PER_RAGE_POINT[lv - 1]!
  return Math.max(0, rage) * perPoint
}

/**
 * 尽情挥发：有效爆裂间隔（秒）
 * 模型：冷却回复速度倍率 = 1 + (攻击速度相关加成总和% / 100) × (尽情挥发档位% / 100)
 * 有效间隔 = 基础 0.3s / 回复倍率
 */
export function effectiveBurstIntervalSec(
  attackSpeedRelatedBonusPct: number,
  jingqingTraitLv: number,
  baseCdSec: number = BURST_BASE_CD_SEC
): { recoveryMult: number; intervalSec: number } {
  const lv = clampTraitLevel(jingqingTraitLv)
  const applyPct = JINGQING_AS_TO_BURST_CD_PCT[lv - 1]! / 100
  const asPart = Math.max(0, attackSpeedRelatedBonusPct) / 100
  const recoveryMult = 1 + asPart * applyPct
  const base = Number.isFinite(baseCdSec) && baseCdSec > 0 ? baseCdSec : BURST_BASE_CD_SEC
  const intervalSec = base / Math.max(recoveryMult, 1e-6)
  return { recoveryMult, intervalSec }
}
