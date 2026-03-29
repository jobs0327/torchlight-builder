/**
 * 伤害 / 战斗相关词条分类与匹配配置（单一数据源，供解析与文档对齐）。
 *
 * 【维护约定】
 * - 说明性字段（label、pool、中文注释）给后期改文案、对表用；`match` 须与真实解析逻辑一致。
 * - 改游戏内词条格式时：先改 `weaponPhysicalFromEquipment.ts`、`BuildCalc.vue` 等实现，再同步本文件。
 * - `implementationRef` 仅为人肉检索用，不参与运行。
 *
 * 【字段速查】
 * - `pool`：词条算进哪个「乘区/池」。
 * - `match`：粗筛条件；真正取数仍由解析器完成。
 * - `valueKind`：数值形态说明，便于以后把解析改成读配置驱动。
 */

// ---------------------------------------------------------------------------
// 乘区 / 池（DamageStatPool）
// 与数据计算页演示模型对应；改 DPS 公式时先想清楚属于哪一池再改 id。
// ---------------------------------------------------------------------------

export type DamageStatPool =
  /** 攻击基础点伤（flat）：武器白字、该装备附加物理、主手武器附加物理等，进「基础点伤」再乘全局 inc/more */
  | 'attack_base_flat'
  /**
   * 双手武器专用：其它装备上的「% 双手武器基础伤害」inc。
   * 演示里乘在「(白字+该装备附加)×本地%该装备物理」这一段上，不进全局伤害 inc 加法池。
   */
  | 'two_handed_weapon_base_inc_pct'
  /** 仅武器上的「% 该装备物理伤害」，本地乘区，先作用于武器 flat 再叠双手基础 inc 等 */
  | 'weapon_local_inc_physical_pct'
  /** 全局伤害提高（inc）：天赋/追忆等文本里「伤害类关键词」旁的 %，加法池 */
  | 'global_damage_inc_pct'
  /** 持续伤害提高（inc）：邻域须含「持续伤害」，与击中类 inc 池分离（BuildCalc 第 7 节） */
  | 'dot_damage_inc_pct'
  /** 全局伤害额外（more）：手填列表 + 技能辅助等，各自连乘 */
  | 'global_damage_more_pct'
  /** 暴击值（百分比形式，装备词条常见「X% 暴击值」） */
  | 'crit_value_pct'
  /** 暴击值（固定值，非 %） */
  | 'crit_value_flat'
  /** 暴击伤害 / 暴击时倍率（演示多为手填） */
  | 'crit_damage_multiplier'
  /** 攻击速度提高（inc%，加法池） */
  | 'attack_speed_inc_pct'
  /** 攻击速度额外（more%，连乘） */
  | 'attack_speed_more_pct'
  /** 施法速度提高（inc%） */
  | 'cast_speed_inc_pct'
  /** 施法速度额外（more%） */
  | 'cast_speed_more_pct'
  /** 武器面板上「±X 攻击速度」白字，单位：次/秒，非百分比 */
  | 'attack_base_speed_flat'
  /**
   * 伤害转化：X% A 转化为 B，或 A 转化为 B（无百分数，如物理→火焰）（装备等）。
   * 独立模块展示/解析，当前不并入简化 DPS 公式。
   */
  | 'damage_conversion'
  /** 明确不计入当前演示基础、或仅能手填/其它口径处理的词条类型 */
  | 'excluded_or_manual'

// ---------------------------------------------------------------------------
// 取值形态（DamageStatValueKind）
// 说明「若实现配置驱动解析，应按哪种方式从字符串里抠数字」。
// ---------------------------------------------------------------------------

export type DamageStatValueKind =
  /** 仅占位，无数值 */
  | 'none'
  /** 武器白字：整行「最小-最大 物理伤害」取区间中值 */
  | 'weapon_white_physical_mid'
  /** 点物理：双括号区间 (a-b)-(c-d) 点物理伤害 类，取双区间中值再平均 */
  | 'dual_range_physical_flat_mid'
  /** 点物理：代入下拉后「X - Y 点物理伤害」两数字取中值 */
  | 'plain_pair_physical_flat_mid'
  /** 该装备附加/攻击附加：多种书写混排（括号+Plain、数-(区间) 等），由专用函数解析 */
  | 'gongzhuang_added_mixed_physical_flat'
  /** 一行内多段 x%，按段求和（如高塔多段 ±%） */
  | 'percent_sum_segments'
  /** 取第一个「%」前的数字或括号区间中值（攻速%、暴击值% 等单行常用） */
  | 'percent_before_first_percent_sign'
  /** 整行即「数字 攻击速度」，武器基础攻速 */
  | 'attack_speed_line_value'
  /** 「暴击值」前、百分号附近的数值 */
  | 'crit_value_pct_before_keyword'
  /** 无百分号的暴击值 flat，在「暴击值」关键词前取数 */
  | 'crit_value_flat_before_keyword'
  /** 用户手填或 UI 合成，非单条 effectPlain 直接解析 */
  | 'hand_or_composite'
  /** 伤害转化：可选百分数 + 「转化为」前后文案片段（无 % 时 pct 为空） */
  | 'damage_conversion_pct_snippets'

// ---------------------------------------------------------------------------
// 单条规则的匹配条件（DamageStatRuleMatch）
// 用于 effectLineMatchesRule 粗筛；与解析器内部条件应对齐。
// ---------------------------------------------------------------------------

export type DamageStatRuleMatch = {
  /**
   * 规范化后的行内须**全部**出现的子串（AND）。
   * 改关键词时注意不要误伤其它词条（宁可多写 exclude）。
   */
  requireAll?: string[]
  /**
   * 多组「组内全部包含即满足」（OR of AND）。
   * 例：主手武器+基底 或 主手武器+基础伤害，二选一成立即可。
   */
  requireAnyOfGroups?: string[][]
  /** 行内出现**任意**一个子串则整条规则不匹配（黑名单） */
  excludeIfIncludes?: string[]
  /** 规范化后行尾必须等于这些后缀之一（OR）；用于强制「点物理伤害」结尾等 */
  mustEndWith?: string[]
  /**
   * 整行须通过该正则（new RegExp(source)）。
   * 改 pattern 后记得在装备样例上测一遍，注意转义。
   */
  mustMatchRegexSource?: string
}

// ---------------------------------------------------------------------------
// 单条规则（DamageStatRule）
// ---------------------------------------------------------------------------

export type DamageStatRule = {
  /** 稳定英文 id，被代码引用时不要改字符串，除非同步改所有引用 */
  id: string
  /** 归属乘区，见 DamageStatPool 注释 */
  pool: DamageStatPool
  /** 给策划/ UI 看的中文名称 */
  labelZh: string
  /** 补充说明：适用场景、与游戏原文差异、是否已实现解析等 */
  descriptionZh?: string
  /**
   * attack：仅攻击技能相关；spell：仅法术；both：天赋追忆等两边都可能吃到
   */
  skillKind: 'attack' | 'spell' | 'both'
  /** 数值怎么从字符串里取，见 DamageStatValueKind */
  valueKind: DamageStatValueKind
  /** 粗匹配条件 */
  match: DamageStatRuleMatch
  /** 实现位置：模块.函数名 或 Vue 内变量，仅文档用 */
  implementationRef?: string
}

/** 配置版本号；做大范围破坏性调整时可递增，便于存档/迁移脚本识别 */
export const DAMAGE_STAT_MATCH_VERSION = 1 as const

/**
 * 全部规则表。
 * 【注意】数组顺序**不表示**优先级；同一行可能被多条规则「粗匹配」命中，最终以解析器为准。
 */
export const damageStatMatchRules: readonly DamageStatRule[] = [
  // ——————————————————————————————————————————————————————————————————————
  // 攻击基础点伤（flat）
  // ——————————————————————————————————————————————————————————————————————

  /** 武器基底：面板白字物理，整行仅「数字-数字 物理伤害」 */
  {
    id: 'weapon_white_physical',
    pool: 'attack_base_flat',
    labelZh: '武器白字物理（最小–最大 物理伤害）',
    descriptionZh: '主手武器行首「数字 - 数字 物理伤害」，取区间中值。勿把带词缀前缀的整行误当白字。',
    skillKind: 'attack',
    valueKind: 'weapon_white_physical_mid',
    match: {
      // 改白字格式（如加「火焰伤害」）时需同步改 parseWeaponBasePhysicalLine 与本正则
      mustMatchRegexSource: String.raw`^\d+(?:\.\d+)?\s*-\s*\d+(?:\.\d+)?\s*物理伤害\s*$`
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseWeaponBasePhysicalLine'
  },

  /** 武器/装备上「该装备附加 … 点物理伤害」；含区间代入后的 Plain 形式 */
  {
    id: 'equip_added_physical',
    pool: 'attack_base_flat',
    labelZh: '该装备附加 … 点物理伤害',
    descriptionZh:
      '含双括号区间、装备页代入下拉后的「X - Y 点物理伤害」、以及「数 - (a-b)」等变体。与「该装备物理伤害」% 词区分。',
    skillKind: 'attack',
    valueKind: 'gongzhuang_added_mixed_physical_flat',
    match: {
      requireAll: ['该装备附加', '点物理伤害']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseGongzhuangAddedPhysical'
  },

  /** 任意部位「主手武器附加 … 点物理伤害」，平加不进武器本地 % 乘区 */
  {
    id: 'main_hand_weapon_added_physical',
    pool: 'attack_base_flat',
    labelZh: '主手武器附加 … 点物理伤害',
    descriptionZh: '其它部位（含双持副手）与主手武器上均可出现；不乘 %该装备物理。',
    skillKind: 'attack',
    valueKind: 'dual_range_physical_flat_mid',
    match: {
      requireAll: ['点物理伤害'],
      mustMatchRegexSource: String.raw`主手武器\s*附加`
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseMainHandWeaponAddedPhysicalFlat'
  },

  /**
   * 【预留】主手武器「基底/基础」点物理类词条。
   * 若数据中确有此类文案，在 parse 里实现后把本规则 match 收紧，避免误匹配。
   */
  {
    id: 'main_hand_weapon_base_damage_flat_placeholder',
    pool: 'attack_base_flat',
    labelZh: '主手武器基底伤害（点物理类，若数据中出现）',
    descriptionZh: '当前解析器未单独实现；仅配置占位。实现后请改 valueKind / implementationRef。',
    skillKind: 'attack',
    valueKind: 'dual_range_physical_flat_mid',
    match: {
      requireAll: ['点物理伤害'],
      requireAnyOfGroups: [
        ['主手武器', '基底'],
        ['主手武器', '基础伤害']
      ]
    }
  },

  /** 手套等上的「额外 X% 双手武器基础伤害」；排除副手武器专用词 */
  {
    id: 'two_handed_weapon_base_damage_inc',
    pool: 'two_handed_weapon_base_inc_pct',
    labelZh: '其它来源 % 双手武器基础伤害',
    descriptionZh: '仅主手为双手武器时生效；加总后乘在武器本地 flat 段（白字+该装备附加已乘本地%）上。',
    skillKind: 'attack',
    valueKind: 'percent_before_first_percent_sign',
    match: {
      requireAll: ['双手武器', '基础伤害', '%'],
      excludeIfIncludes: ['副手武器']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseTwoHandedWeaponBaseDamageIncPct'
  },

  /** 武器上「攻击附加」物理：当前约定不进演示基础点伤 */
  {
    id: 'attack_added_physical_on_weapon',
    pool: 'excluded_or_manual',
    labelZh: '攻击附加 … 点物理伤害（武器上）',
    descriptionZh: '若以后要并入某池，改 pool 与 estimatePhysicalAttackFlatFromEquipment 逻辑，并更新此处说明。',
    skillKind: 'attack',
    valueKind: 'gongzhuang_added_mixed_physical_flat',
    match: {
      requireAll: ['攻击附加', '点物理伤害']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseAttackAddedPhysical'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 武器本地 inc（仅 % 该装备物理伤害）
  // ——————————————————————————————————————————————————————————————————————

  /** 近战伤害、攻击伤害等 inc 不在此池，勿把关键词写进本规则 */
  {
    id: 'local_equip_physical_inc_pct',
    pool: 'weapon_local_inc_physical_pct',
    labelZh: '% 该装备物理伤害（本地，可多段 ±）',
    descriptionZh: '必须含「该装备物理伤害」六字，与「该装备附加」点伤区分。',
    skillKind: 'attack',
    valueKind: 'percent_sum_segments',
    match: {
      requireAll: ['该装备物理伤害', '%']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseLocalIncPhysicalPctContributions'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 全局伤害 inc（天赋 / 追忆等，BuildCalc 文本解析）
  // ——————————————————————————————————————————————————————————————————————

  /**
   * 关键词邻近 % 的粗筛；真正关键词列表在 BuildCalc.extractPctValuesByKeywords 里。
   * 增删关键词（如「近战伤害」是否算 inc）须同时改 BuildCalc 与本条 descriptionZh。
   * 【注意】同一 % 若邻近窗口内出现「额外」，不计入伤害 inc（视为 more/独立乘区口径）。
   * 【注意】按子句切分后，含「转化为」的片段整段不计入伤害 inc（转伤类归 damage_conversion 独立解析）。
   * 【注意】子句拆分见 BuildCalc.splitLineIntoEffectClauses（标点、和/与/及/以及、连续 %+ 段），避免一行内玩家与召唤物加成混在同一段。
   * 【注意】全局玩家伤害 inc 子句排除：召唤物/魔灵/智械、转移至/伤害转移、非哨卫核心时的哨卫文案（见 effectClauseSkipForPlayerGlobalDamageInc）。
   */
  {
    id: 'global_damage_inc_keywords',
    pool: 'global_damage_inc_pct',
    labelZh: '伤害提高类 inc（关键词邻近 x%）',
    descriptionZh:
      '实现侧关键词：伤害、增伤、伤害提高、攻击伤害、法术伤害、元素伤害。排除：邻近窗口含「额外」的 %；邻域含「持续伤害」「异常伤害」（专用池）；同一子句含「转化为」；子句含「转移至」「伤害转移」；子句含召唤物/魔灵/智械；非哨卫核心时含哨卫/哨位。',
    skillKind: 'both',
    valueKind: 'percent_sum_segments',
    match: {
      requireAll: ['%']
    },
    implementationRef:
      'BuildCalc.splitLineIntoEffectClauses + effectClauseSkipForPlayerGlobalDamageInc + extractDamageIncPctValuesFromLine + resolvePctBucketsFromEffectLinesDetailed'
  },

  {
    id: 'dot_damage_inc_keywords',
    pool: 'dot_damage_inc_pct',
    labelZh: '持续伤害提高类 inc（关键词邻近 x%）',
    descriptionZh:
      '邻域须含「持续伤害」；关键词列表见 BuildCalc.extractDotDamageIncPctValuesFromLine。子句级排除与击中池共用（转化为、召唤侧、转嫁、哨卫等）。',
    skillKind: 'both',
    valueKind: 'percent_sum_segments',
    match: {
      requireAll: ['%', '持续伤害']
    },
    implementationRef:
      'BuildCalc.extractDotDamageIncPctValuesFromLine + resolvePctBucketsFromEffectLinesDetailed.dotDamageSources'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 全局伤害 more（手填 + 技能链路）
  // ——————————————————————————————————————————————————————————————————————

  /** 无单行 match；由输入框与技能 meta 驱动 */
  {
    id: 'global_damage_more_hand_list',
    pool: 'global_damage_more_pct',
    labelZh: '伤害 more（手填逗号列表）',
    descriptionZh: '含辅助技能 more、被动链路合并等，见 skillDerivedSummary。',
    skillKind: 'both',
    valueKind: 'hand_or_composite',
    match: {},
    implementationRef: 'BuildCalc.dmgMoreListStr + skillDerivedSummary.damageMoreSources'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 暴击值
  // ——————————————————————————————————————————————————————————————————————

  /** 装备「X% 暴击值」类 */
  {
    id: 'crit_value_pct_equipment',
    pool: 'crit_value_pct',
    labelZh: '% 暴击值',
    descriptionZh: '须同时含 % 与 暴击值；解析取百分号前数字。',
    skillKind: 'attack',
    valueKind: 'crit_value_pct_before_keyword',
    match: {
      requireAll: ['%', '暴击值']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseCritValuePct'
  },

  /** 固定暴击值，行内无 % */
  {
    id: 'crit_value_flat_equipment',
    pool: 'crit_value_flat',
    labelZh: '暴击值（平，攻击/攻击和法术等）',
    descriptionZh: '与 % 暴击值互斥筛选：flat 解析要求行内不出现百分号（实现见 parseCritValueFlat）。',
    skillKind: 'attack',
    valueKind: 'crit_value_flat_before_keyword',
    match: {
      mustMatchRegexSource: String.raw`攻击和法术暴击值|攻击暴击值|暴击值`
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseCritValueFlat'
  },

  /** 被动技能 JSON / 描述解析出的暴击值加总 */
  {
    id: 'crit_value_passive_parsed',
    pool: 'crit_value_pct',
    labelZh: '被动技能暴击值（面板/描述解析）',
    descriptionZh: '非单条装备行 match；仅占位说明数据来源。',
    skillKind: 'both',
    valueKind: 'percent_sum_segments',
    match: {},
    implementationRef: 'BuildCalc.skillDerivedSummary.critValuePct'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 暴击伤害（倍率）
  // ——————————————————————————————————————————————————————————————————————

  /** 演示页手填暴击倍率；游戏词条若单独拆出可另加规则 */
  {
    id: 'crit_strike_multiplier_hand',
    pool: 'crit_damage_multiplier',
    labelZh: '暴击时伤害倍率（相对不暴击）',
    descriptionZh: '当前多为手填；若从装备扫「暴击伤害」%，需新增规则并实现解析。',
    skillKind: 'both',
    valueKind: 'hand_or_composite',
    match: {},
    implementationRef: 'BuildCalc.dmgCritMult'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 攻击速度
  // ——————————————————————————————————————————————————————————————————————

  /** 武器单独一行「数字 攻击速度」= 基础每秒攻击次数 */
  {
    id: 'weapon_base_attack_speed_line',
    pool: 'attack_base_speed_flat',
    labelZh: '武器「±X 攻击速度」白字行',
    descriptionZh: '与「X% 攻击速度」区分：本条无百分号，整行匹配。',
    skillKind: 'attack',
    valueKind: 'attack_speed_line_value',
    match: {
      mustMatchRegexSource: String.raw`^[+-]?\d+(?:\.\d+)?\s*攻击速度\s*$`
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseBaseAttackSpeed'
  },

  /** 装备词条「攻击速度」且带 % */
  {
    id: 'attack_speed_inc_pct',
    pool: 'attack_speed_inc_pct',
    labelZh: '% 攻击速度提高',
    descriptionZh: '取百分号前数值；与「施法速度」勿混。',
    skillKind: 'attack',
    valueKind: 'percent_before_first_percent_sign',
    match: {
      requireAll: ['攻击速度', '%']
    },
    implementationRef: 'weaponPhysicalFromEquipment.parseAttackSpeedIncPct'
  },

  /** 天赋/追忆效果行：关键词 攻击速度 / 攻速 邻近的 % */
  {
    id: 'attack_speed_inc_keywords_talent_memory',
    pool: 'attack_speed_inc_pct',
    labelZh: '攻击速度 inc（天赋/追忆等：攻速/攻击速度 邻近 %）',
    descriptionZh: '具体邻域宽度见 BuildCalc.extractPctValuesByKeywords 实现。',
    skillKind: 'attack',
    valueKind: 'percent_sum_segments',
    match: {},
    implementationRef: 'BuildCalc.extractPctValuesByKeywords (攻击速度, 攻速)'
  },

  /** 速率 more 与法术共用同一手填框（攻击模式下当攻速 more） */
  {
    id: 'attack_speed_more_hand',
    pool: 'attack_speed_more_pct',
    labelZh: '攻击速度 more（手填逗号列表）',
    descriptionZh: 'BuildCalc 中攻击技能时使用 dmgSpeedMoreStr。',
    skillKind: 'attack',
    valueKind: 'hand_or_composite',
    match: {},
    implementationRef: 'BuildCalc.dmgSpeedMoreStr'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 施法速度
  // ——————————————————————————————————————————————————————————————————————

  /** 施法速度 / 施法 关键词邻近 % */
  {
    id: 'cast_speed_inc_keywords',
    pool: 'cast_speed_inc_pct',
    labelZh: '施法速度 inc（施法速度/施法 邻近 %）',
    descriptionZh: '「施法」易与其它词粘连，改关键词时检查误匹配。',
    skillKind: 'spell',
    valueKind: 'percent_sum_segments',
    match: {},
    implementationRef: 'BuildCalc.extractPctValuesByKeywords (施法速度, 施法)'
  },

  /** 与攻击共用 dmgSpeedMoreStr，法术模式下语义为施法 more */
  {
    id: 'cast_speed_more_hand',
    pool: 'cast_speed_more_pct',
    labelZh: '施法速度 more（手填逗号列表）',
    descriptionZh: 'BuildCalc 中法术技能时使用同一输入框。',
    skillKind: 'spell',
    valueKind: 'hand_or_composite',
    match: {},
    implementationRef: 'BuildCalc.dmgSpeedMoreStr'
  },

  // ——————————————————————————————————————————————————————————————————————
  // 伤害转化（独立模块，装备快照）
  // ——————————————————————————————————————————————————————————————————————

  /**
   * 粗筛：须含「转化为」（可有 X%，也可无，如「物理伤害转化为火焰伤害」）；拆条见 damageConversionFromEquipment。
   * BuildCalc 中装备 / 天赋原文 / 追忆 / 契灵 / 英雄特性等统一经 estimateDamageConversionFromSourceBundles 解析；勿与 inc 池混算。
   */
  {
    id: 'damage_conversion_equipment_line',
    pool: 'damage_conversion',
    labelZh: '伤害转化（X% … 转化为 … / … 转化为 …）',
    descriptionZh:
      '典型：30% 闪电伤害转化为冰冷、物理伤害转化为火焰伤害、受到的物理伤害转化为元素等；条件前缀保留在 from 片段中。',
    skillKind: 'both',
    valueKind: 'damage_conversion_pct_snippets',
    match: {
      requireAll: ['转化为']
    },
    implementationRef:
      'damageConversionFromEquipment: estimateDamageConversionFromSourceBundles / estimateDamageConversionFromEquipment + parseDamageConversionSegmentsFromLine'
  }
]

// ---------------------------------------------------------------------------
// 池的中文说明表（给 UI 或文档生成用）
// ---------------------------------------------------------------------------

export type DamageStatPoolMeta = {
  /** 与 DamageStatPool 一致 */
  id: DamageStatPool
  /** 短标题 */
  labelZh: string
  /** 与演示公式、游戏差异的备注 */
  hintZh?: string
}

export const damageStatPoolMeta: readonly DamageStatPoolMeta[] = [
  /** 攻击技能「基础点伤」相关 flat 的总口径说明 */
  { id: 'attack_base_flat', labelZh: '攻击基础点伤（flat 合计相关）' },
  {
    id: 'two_handed_weapon_base_inc_pct',
    labelZh: '双手武器基础伤害（inc%，其它装备来源）',
    hintZh: '演示中与武器本地 flat 段相乘，不并入全局 inc 池。'
  },
  {
    id: 'weapon_local_inc_physical_pct',
    labelZh: '武器本地 % 该装备物理伤害',
    hintZh: '与其它全局 inc 分离，先乘在武器 flat 段上。'
  },
  /** 加法池：所有 inc% 先加再乘到伤害上 */
  { id: 'global_damage_inc_pct', labelZh: '伤害提高（inc，加法池 · 击中类）' },
  {
    id: 'dot_damage_inc_pct',
    labelZh: '持续伤害提高（inc，独立加法池）',
    hintZh: '与击中类 global_damage_inc 解析分离；见 BuildCalc 持续伤害模块。'
  },
  /** 每条 more 独立连乘 */
  { id: 'global_damage_more_pct', labelZh: '伤害额外（more，连乘）' },
  { id: 'crit_value_pct', labelZh: '暴击值（%）' },
  { id: 'crit_value_flat', labelZh: '暴击值（平）' },
  { id: 'crit_damage_multiplier', labelZh: '暴击伤害 / 暴击倍率' },
  { id: 'attack_speed_inc_pct', labelZh: '攻击速度提高（inc）' },
  { id: 'attack_speed_more_pct', labelZh: '攻击速度额外（more）' },
  { id: 'cast_speed_inc_pct', labelZh: '施法速度提高（inc）' },
  { id: 'cast_speed_more_pct', labelZh: '施法速度额外（more）' },
  { id: 'attack_base_speed_flat', labelZh: '基础攻击速度（次/秒，武器白字）' },
  {
    id: 'damage_conversion',
    labelZh: '伤害转化',
    hintZh: '单独列表展示；与 inc/more/基础点伤乘区分离，不参与当前演示 DPS 连乘。'
  },
  { id: 'excluded_or_manual', labelZh: '排除或仅手填/其它口径' }
]

// ---------------------------------------------------------------------------
// 内部：与解析器一致的轻量规范化
// ---------------------------------------------------------------------------

/** 统一 Unicode 破折号为 ASCII，并 trim，便于和装备行比对 */
function normLine(s: string): string {
  return s.replace(/[–—]/g, '-').trim()
}

/** 去掉自制/展示用前缀如 [初阶前缀]，与 weaponPhysicalFromEquipment.stripLeadingEffectLineTag 行为一致 */
function stripLeadingTag(s: string): string {
  return normLine(s).replace(/^\[[^\]]+\]\s*/, '')
}

// ---------------------------------------------------------------------------
// 导出工具函数
// ---------------------------------------------------------------------------

/**
 * 粗匹配：判断一行效果**是否可能**属于某规则。
 * 【注意】不等于游戏内真实结算；数值提取仍以各 parse 函数为准。
 */
export function effectLineMatchesRule(rule: DamageStatRule, rawLine: string): boolean {
  const line = stripLeadingTag(rawLine)
  const m = rule.match

  if (m.excludeIfIncludes?.some(k => line.includes(k))) return false

  if (m.requireAll?.length) {
    for (const k of m.requireAll) {
      if (!line.includes(k)) return false
    }
  }

  if (m.requireAnyOfGroups?.length) {
    const ok = m.requireAnyOfGroups.some(group => group.every(k => line.includes(k)))
    if (!ok) return false
  }

  for (const suf of m.mustEndWith ?? []) {
    if (!line.endsWith(suf)) return false
  }

  if (m.mustMatchRegexSource) {
    try {
      const re = new RegExp(m.mustMatchRegexSource)
      if (!re.test(line)) return false
    } catch {
      return false
    }
  }

  return true
}

/** 按乘区 id 筛选规则，方便按池浏览配置 */
export function rulesForPool(pool: DamageStatPool): DamageStatRule[] {
  return damageStatMatchRules.filter(r => r.pool === pool)
}

/**
 * 列出某技能类型会涉及到的池元数据（去重）。
 * 用于以后做「攻击/法术」分栏说明页。
 */
export function poolsForSkillKind(kind: 'attack' | 'spell'): DamageStatPoolMeta[] {
  const ids = new Set(
    damageStatMatchRules.filter(r => r.skillKind === kind || r.skillKind === 'both').map(r => r.pool)
  )
  return damageStatPoolMeta.filter(p => ids.has(p.id))
}
