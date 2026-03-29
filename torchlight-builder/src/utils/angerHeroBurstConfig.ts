/**
 * 怒火英雄「爆裂」：数据在 heroes.json 的 burstSkill（游戏内机制技能，非 activeSkillTags 条目）。
 */

import { BURST_BASE_CD_SEC } from '@/utils/heroAngerBurst'

export type HeroBurstSkillJson = {
  name?: string
  /** 范围爆炸：相当于 X% 武器伤害 */
  weaponDamageMultiplierPct?: number
  /** 每 +1 技能等级额外伤害，叠乘（如 1.1 表示每级 ×1.1） */
  perSkillLevelMoreMultiplicative?: number
  /** 作用半径（米） */
  radiusMeters?: number
  baseCooldownSec?: number
  /** 与面板一致的标签 */
  tags?: string[]
  /** 补充说明（如双持规则） */
  notes?: string[]
  /** @deprecated 使用 weaponDamageMultiplierPct */
  hitDamageMultiplierPct?: number
}

export type AngerHeroJson = {
  id?: string
  traits?: { name?: string; effects?: string[] }[]
  burstSkill?: HeroBurstSkillJson
}

const RE_BURST_CD = /冷却时间为\s*(\d+(?:\.\d+)?)\s*秒/

export const DEFAULT_BURST_WEAPON_DAMAGE_PCT = 340
export const DEFAULT_BURST_PER_LEVEL_MORE = 1.1
export const DEFAULT_BURST_RADIUS_M = 3

export type ResolvedAngerBurstSkill = {
  skillName: string
  radiusMeters: number
  weaponDamageMultiplierPct: number
  perSkillLevelMoreMultiplicative: number
  baseCooldownSec: number
  tags: string[]
  notes: string[]
}

export function resolveAngerBurstSkill(hero: unknown): ResolvedAngerBurstSkill {
  const h = hero as AngerHeroJson
  const bs = h?.burstSkill ?? {}
  const fury = h?.traits?.find(t => t?.name === '怒火')
  const text = (fury?.effects ?? []).join('\n')

  let baseCd = BURST_BASE_CD_SEC
  const mcd = text.match(RE_BURST_CD)
  if (mcd) {
    const v = parseFloat(mcd[1]!)
    if (Number.isFinite(v) && v > 0) baseCd = v
  }
  if (
    typeof bs.baseCooldownSec === 'number' &&
    Number.isFinite(bs.baseCooldownSec) &&
    bs.baseCooldownSec > 0
  ) {
    baseCd = bs.baseCooldownSec
  }

  const wPct =
    typeof bs.weaponDamageMultiplierPct === 'number' && bs.weaponDamageMultiplierPct > 0
      ? bs.weaponDamageMultiplierPct
      : typeof bs.hitDamageMultiplierPct === 'number' && bs.hitDamageMultiplierPct > 0
        ? bs.hitDamageMultiplierPct
        : DEFAULT_BURST_WEAPON_DAMAGE_PCT

  const more =
    typeof bs.perSkillLevelMoreMultiplicative === 'number' &&
    bs.perSkillLevelMoreMultiplicative > 0
      ? bs.perSkillLevelMoreMultiplicative
      : DEFAULT_BURST_PER_LEVEL_MORE

  const radius =
    typeof bs.radiusMeters === 'number' && bs.radiusMeters > 0
      ? bs.radiusMeters
      : DEFAULT_BURST_RADIUS_M

  return {
    skillName: (bs.name ?? '爆裂').trim() || '爆裂',
    radiusMeters: radius,
    weaponDamageMultiplierPct: wPct,
    perSkillLevelMoreMultiplicative: more,
    baseCooldownSec: baseCd,
    tags: Array.isArray(bs.tags) ? bs.tags.map(String) : [],
    notes: Array.isArray(bs.notes) ? bs.notes.map(String) : []
  }
}

/**
 * 爆裂「技能本体」相对武器伤害的乘数： (武器伤害%÷100) × more^(等级−1)，等级从 1 起算。
 */
export function burstSkillWeaponPartMultiplier(
  weaponDamageMultiplierPct: number,
  skillLevel: number,
  perSkillLevelMore: number
): number {
  const lv = Math.max(1, Math.floor(skillLevel))
  const w = Math.max(0, weaponDamageMultiplierPct) / 100
  return w * Math.pow(perSkillLevelMore, lv - 1)
}

export function getAngerHeroFromList(heroes: unknown): AngerHeroJson | null {
  if (!Array.isArray(heroes)) return null
  const h = heroes.find((x: { id?: string }) => x?.id === 'Anger')
  return (h as AngerHeroJson) ?? null
}
