/**
 * 火炬之光：无限 —— **简化伤害估算**（非官方、用于 BD 工具演示）
 *
 * **基础点伤来源（与常见设定对齐，便于接装备/技能数据）：**
 * - **攻击类技能**：一次击中的**基础点伤**来自**当前武器（主手/双持规则下）的基础伤害**（面板上的物理/元素等，可先合并为单一数值做演示）。
 * - **法术类技能**：基础点伤通常来自**技能自带的固定基数 / 等级成长**（`skillBaseDamage` 等），**不**再吃武器平砍白字（除非游戏内另有「攻击法术」特例，此处不拆）。
 *
 * 约定（类 PoE / 常见 ARPG 结构，与游戏内真实跳字可能不一致）：
 * 1. **「提高 / inc」**：同一标签池内先 **加总** → 乘区 `1 + Σ(提高%)/100`
 * 2. **「额外 / more」**：每条独立 **连乘** → `Π(1 + 额外_i%)`
 * 3. **单次期望伤害**：`基础 × 伤害inc × 伤害more × 抗性 × 暴击期望 × 其他独立乘区`
 * 4. **暴击期望**：`期望倍率 = 1 + 暴击率 × (暴击时总倍率 − 1)`
 * 5. **抗性**：`承受 = max(0, 1 − min(抗性%, 100%)/100)`（不做穿透细拆）
 * 6. **攻速 / 施法**：**攻击**标签技能用 **攻击速度**；**法术**标签技能用 **施法速度**。每秒次数 =
 *    `基础每秒次数 × (1 + 对应速率的 inc 总和/100) × Π(1 + 对应 more%)`
 * 7. **DPS**：`单次期望伤害 × 每秒次数`（演示用；持续、引导、多段等未拆）
 */

/** 技能伤害所吃「基础点伤」的来源类型（演示用） */
export type SkillBaseDamageKind = 'attack' | 'spell'

/**
 * 解析进入乘法链的 **单次击中基础点伤**。
 * - `attack`：使用 `weaponBaseFlat`（来自武器面板，可后续接主手装备 JSON）。
 * - `spell`：使用 `skillBaseFlat`（来自技能等级表/面板）。
 */
export function effectiveBaseFlatDamage(input: {
  kind: SkillBaseDamageKind
  weaponBaseFlat?: number
  skillBaseFlat?: number
}): number {
  if (input.kind === 'attack') {
    const w = input.weaponBaseFlat
    return Math.max(0, Number.isFinite(w as number) ? (w as number) : 0)
  }
  const s = input.skillBaseFlat
  return Math.max(0, Number.isFinite(s as number) ? (s as number) : 0)
}

export type HitDamageBreakdown = {
  /** 进入公式的单次击中基础点伤（已按攻击/法术规则解析） */
  base: number
  /** 若传入，标明基础点伤来自武器还是技能 */
  baseKind?: SkillBaseDamageKind
  increasedPctTotal: number
  increasedMultiplier: number
  morePctList: number[]
  moreMultiplier: number
  enemyResistPct: number
  resistMultiplier: number
  critChance: number
  critStrikeMultiplier: number
  critExpectedMultiplier: number
  /** 其他独立乘区（易伤、环境等，默认 1） */
  otherIndependentMultiplier: number
  /** 单次击中「期望」伤害（未模拟波动） */
  expectedDamage: number
}

/** 攻速或施法：每秒攻击/施法次数 */
export type HitsPerSecondBreakdown = {
  /** 面板基础：武器「每秒攻击」或技能侧基础施法频率（次/秒） */
  basePerSecond: number
  speedIncreasedPctTotal: number
  speedIncreasedMultiplier: number
  speedMorePctList: number[]
  speedMoreMultiplier: number
  hitsPerSecond: number
}

export type DpsBreakdown = {
  hit: HitDamageBreakdown
  speed: HitsPerSecondBreakdown
  /** 技能标签：攻击 → 用攻速；法术 → 用施法 */
  speedAppliesTo: SkillBaseDamageKind
  dps: number
}

function clamp(n: number, lo: number, hi: number): number {
  return Math.min(hi, Math.max(lo, n))
}

/** 提高类加法池 → 单一乘区 */
export function increasedMultiplierFromTotal(increasedPctTotal: number): number {
  return 1 + increasedPctTotal / 100
}

/** 每条「额外 X%」独立相乘 */
export function moreMultiplierFromList(morePctList: number[]): number {
  let m = 1
  for (const p of morePctList) {
    if (!Number.isFinite(p)) continue
    m *= 1 + p / 100
  }
  return m
}

/** 敌人抗性（0–100）→ 承受乘区 */
export function resistMultiplier(enemyResistPct: number): number {
  const r = clamp(enemyResistPct, 0, 100)
  return Math.max(0, 1 - r / 100)
}

/**
 * 暴击期望倍率
 * @param critChance 0–1
 * @param critStrikeMultiplier 暴击时相对 **不暴击** 的总倍率（例：2.5 = 暴击为不暴击的 2.5 倍）
 */
export function critExpectedMultiplier(critChance: number, critStrikeMultiplier: number): number {
  const cc = clamp(critChance, 0, 1)
  const cm = Math.max(1, critStrikeMultiplier)
  return 1 + cc * (cm - 1)
}

export function estimateExpectedHitDamage(input: {
  base: number
  /** 可选：用于展示「基础点伤来自武器/技能」 */
  baseKind?: SkillBaseDamageKind
  increasedPctTotal: number
  morePctList: number[]
  enemyResistPct: number
  critChance: number
  critStrikeMultiplier: number
  /** 其他独立乘区，默认 1 */
  otherIndependentMultiplier?: number
}): HitDamageBreakdown {
  const base = Math.max(0, input.base)
  const incM = increasedMultiplierFromTotal(input.increasedPctTotal)
  const moreM = moreMultiplierFromList(input.morePctList)
  const resM = resistMultiplier(input.enemyResistPct)
  const critM = critExpectedMultiplier(input.critChance, input.critStrikeMultiplier)
  const otherM =
    input.otherIndependentMultiplier != null && Number.isFinite(input.otherIndependentMultiplier)
      ? Math.max(0, input.otherIndependentMultiplier)
      : 1
  const expectedDamage = base * incM * moreM * resM * critM * otherM

  return {
    base,
    baseKind: input.baseKind,
    increasedPctTotal: input.increasedPctTotal,
    increasedMultiplier: incM,
    morePctList: [...input.morePctList],
    moreMultiplier: moreM,
    enemyResistPct: input.enemyResistPct,
    resistMultiplier: resM,
    critChance: input.critChance,
    critStrikeMultiplier: input.critStrikeMultiplier,
    critExpectedMultiplier: critM,
    otherIndependentMultiplier: otherM,
    expectedDamage
  }
}

/**
 * 每秒攻击次数或每秒施法次数（与技能标签对应：攻击用攻速池，法术用施法池）。
 * `每秒次数 = 基础 × (1 + 速率inc总和/100) × more₁ × more₂ × …`
 */
export function estimateHitsPerSecond(input: {
  basePerSecond: number
  speedIncreasedPctTotal: number
  speedMorePctList: number[]
}): HitsPerSecondBreakdown {
  const basePerSecond = Math.max(0, input.basePerSecond)
  const speedIncM = increasedMultiplierFromTotal(input.speedIncreasedPctTotal)
  const speedMoreM = moreMultiplierFromList(input.speedMorePctList)
  const hitsPerSecond = basePerSecond * speedIncM * speedMoreM
  return {
    basePerSecond,
    speedIncreasedPctTotal: input.speedIncreasedPctTotal,
    speedIncreasedMultiplier: speedIncM,
    speedMorePctList: [...input.speedMorePctList],
    speedMoreMultiplier: speedMoreM,
    hitsPerSecond
  }
}

/** 单次期望 × 每秒次数；`speedKind` 仅用于标注，数值由调用方选对应池。 */
export function estimateDps(hit: HitDamageBreakdown, speed: HitsPerSecondBreakdown, speedKind: SkillBaseDamageKind): DpsBreakdown {
  return {
    hit,
    speed,
    speedAppliesTo: speedKind,
    dps: hit.expectedDamage * speed.hitsPerSecond
  }
}
