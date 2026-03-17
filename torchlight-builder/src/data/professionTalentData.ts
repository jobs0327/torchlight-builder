import type { GodType } from '@/types'

export type TalentNodeType = 'legendary' | 'notable' | 'small'

export interface TalentNodePosition {
  row: number
  col: number
  x: number
  y: number
}

export interface ProfessionTalentNode {
  id: string
  name: string
  type: TalentNodeType
  description: string
  effects: string[]
  requiredPoints: number
  maxPoints: number
  currentPoints: number
  position: TalentNodePosition
  connections: string[]
  icon?: string
}

export interface ProfessionTalentTree {
  id: string
  name: string
  godType: GodType
  description: string
  tags: string[]
  nodes: ProfessionTalentNode[]
  coreTalents: ProfessionTalentNode[]
  totalPoints: number
  allocatedPoints: number
}

// 网格布局配置 - 基于原网站SVG数据
const GRID_CONFIG = {
  nodeWidth: 64,
  nodeHeight: 64,
  rowSpacing: 96,
  colSpacing: 64,
  offsetX: 32,
  offsetY: 0
}

// 层级配置
const LEVELS = [0, 3, 6, 9, 12, 15, 18]

// 勇者天赋树数据 - 基于原网站SVG数据精确还原
export const THE_BRAVE_TREE: ProfessionTalentTree = {
  id: 'the_brave',
  name: '勇者',
  godType: 'strength',
  description: '巨力之神的传承，攻守均衡的战斗大师',
  tags: ['单手武器', '护甲'],
  totalPoints: 36,
  allocatedPoints: 0,
  coreTalents: [
    {
      id: 'core_rujing',
      name: '入静',
      type: 'legendary',
      description: '静止时，每 0.25 秒，额外 +12% 伤害，至多额外 +48% 伤害。失去静止状态时，移除该效果',
      effects: ['静止时，每 0.25 秒，额外 +12% 伤害，至多额外 +48% 伤害', '失去静止状态时，移除该效果'],
      requiredPoints: 18,
      maxPoints: 1,
      currentPoints: 0,
      position: { row: 0, col: 0, x: 150, y: 30 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_rujing_Icon_128.webp'
    },
    {
      id: 'core_daxiangwuxing',
      name: '大象无形',
      type: 'legendary',
      description: '战吼技能的影响上限变为 2 倍，+66% 战吼技能范围',
      effects: ['战吼技能的影响上限变为 2 倍', '+66% 战吼技能范围'],
      requiredPoints: 18,
      maxPoints: 1,
      currentPoints: 0,
      position: { row: 0, col: 1, x: 350, y: 30 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_daxiangwuxing_Icon_128.webp'
    },
    {
      id: 'core_jianyi',
      name: '坚毅',
      type: 'legendary',
      description: '每有 1 层坚韧祝福，额外 +4% 护甲值',
      effects: ['每有 1 层坚韧祝福，额外 +4% 护甲值'],
      requiredPoints: 18,
      maxPoints: 1,
      currentPoints: 0,
      position: { row: 0, col: 2, x: 550, y: 30 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_jianyi_Icon_128.webp'
    },
    {
      id: 'core_huijinzhuangjia',
      name: '灰烬装甲',
      type: 'legendary',
      description: '对非物理伤害，+25% 护甲有效率',
      effects: ['对非物理伤害，+25% 护甲有效率'],
      requiredPoints: 18,
      maxPoints: 1,
      currentPoints: 0,
      position: { row: 0, col: 3, x: 750, y: 30 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Skill/CoreTalentIcon/128/UI_CoreTalentIcon_huijinzhuangjia_Icon_128.webp'
    }
  ],
  nodes: [
    // 第一行 (y=82) - 0, 3, 6, 9, 12, 15, 18
    {
      id: 'row1_col1',
      name: '+9% 攻击伤害',
      type: 'small',
      description: '+9% 攻击伤害',
      effects: ['+9% 攻击伤害'],
      requiredPoints: 0,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 0, x: 136, y: 82 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Dmg_64.webp'
    },
    {
      id: 'row1_col2',
      name: '+18% 攻击伤害',
      type: 'notable',
      description: '+18% 攻击伤害',
      effects: ['+18% 攻击伤害'],
      requiredPoints: 3,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 1, x: 272, y: 82 },
      connections: ['row1_col1'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Atk_64.webp'
    },
    {
      id: 'row1_col3',
      name: '+20% 攻击暴击值',
      type: 'small',
      description: '+20% 攻击暴击值，+5% 暴击伤害',
      effects: ['+20% 攻击暴击值', '+5% 暴击伤害'],
      requiredPoints: 6,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 2, x: 408, y: 82 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Crit_64.webp'
    },
    {
      id: 'row1_col4',
      name: '持单手武器时，+9% 攻击伤害',
      type: 'notable',
      description: '持单手武器时，+9% 攻击伤害',
      effects: ['持单手武器时，+9% 攻击伤害'],
      requiredPoints: 9,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 3, x: 544, y: 82 },
      connections: ['row1_col3'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Atk_64.webp'
    },
    {
      id: 'row1_col5',
      name: '+8 力量',
      type: 'small',
      description: '+8 力量',
      effects: ['+8 力量'],
      requiredPoints: 12,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 4, x: 672, y: 82 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Strength_64.webp'
    },
    {
      id: 'row1_col6',
      name: '持单手武器时，额外 +8% 攻击伤害',
      type: 'notable',
      description: '持单手武器时，额外 +8% 攻击伤害',
      effects: ['持单手武器时，额外 +8% 攻击伤害'],
      requiredPoints: 15,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 0, col: 5, x: 808, y: 82 },
      connections: ['row1_col5'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Atk_64.webp'
    },

    // 第二行 (y=178) - 3, 6, 9, 12, 15, 18
    {
      id: 'row2_col1',
      name: '+6% 攻击速度',
      type: 'notable',
      description: '+6% 攻击速度，-4 技能消耗',
      effects: ['+6% 攻击速度', '-4 技能消耗'],
      requiredPoints: 3,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 1, col: 0, x: 272, y: 178 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Spd_64.webp'
    },
    {
      id: 'row2_col2',
      name: '+4% 攻击速度',
      type: 'small',
      description: '+4% 攻击速度',
      effects: ['+4% 攻击速度'],
      requiredPoints: 6,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 1, col: 1, x: 408, y: 178 },
      connections: ['row2_col1'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Spd_64.webp'
    },
    {
      id: 'row2_col3',
      name: '+8% 攻击速度',
      type: 'notable',
      description: '+8% 攻击速度，-6 技能消耗',
      effects: ['+8% 攻击速度', '-6 技能消耗'],
      requiredPoints: 9,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 1, col: 2, x: 544, y: 178 },
      connections: ['row2_col2'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Spd_64.webp'
    },
    {
      id: 'row2_col4',
      name: '+5% 攻击速度',
      type: 'small',
      description: '+5% 攻击速度',
      effects: ['+5% 攻击速度'],
      requiredPoints: 12,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 1, col: 3, x: 672, y: 178 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Spd_64.webp'
    },
    {
      id: 'row2_col5',
      name: '+10% 攻击速度',
      type: 'notable',
      description: '+10% 攻击速度，-8 技能消耗',
      effects: ['+10% 攻击速度', '-8 技能消耗'],
      requiredPoints: 15,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 1, col: 4, x: 808, y: 178 },
      connections: ['row2_col4'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Spd_64.webp'
    },

    // 第三行 (y=274) - 0, 3, 6, 9, 12, 15, 18
    {
      id: 'row3_col1',
      name: '+7% 护甲值',
      type: 'small',
      description: '+7% 护甲值',
      effects: ['+7% 护甲值'],
      requiredPoints: 0,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 0, x: 136, y: 274 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Armor_64.webp'
    },
    {
      id: 'row3_col2',
      name: '+8% 攻击格挡率',
      type: 'notable',
      description: '+8% 攻击格挡率',
      effects: ['+8% 攻击格挡率'],
      requiredPoints: 3,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 1, x: 272, y: 274 },
      connections: ['row3_col1'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Block_64.webp'
    },
    {
      id: 'row3_col3',
      name: '1.5% 生命返还',
      type: 'small',
      description: '1.5% 生命返还',
      effects: ['1.5% 生命返还'],
      requiredPoints: 6,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 2, x: 408, y: 274 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/HP_64.webp'
    },
    {
      id: 'row3_col4',
      name: '+3% 生命返还',
      type: 'notable',
      description: '+3% 生命返还',
      effects: ['+3% 生命返还'],
      requiredPoints: 9,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 3, x: 544, y: 274 },
      connections: ['row3_col3'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/HP_64.webp'
    },
    {
      id: 'row3_col5',
      name: '受到伤害时获得坚韧祝福',
      type: 'small',
      description: '受到伤害时，+25% 几率获得 1 层坚韧祝福，间隔 1 秒',
      effects: ['受到伤害时，+25% 几率获得 1 层坚韧祝福，间隔 1 秒'],
      requiredPoints: 12,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 4, x: 672, y: 274 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Buff_64.webp'
    },
    {
      id: 'row3_col6',
      name: '+6% 战吼技能的效果',
      type: 'notable',
      description: '+6% 战吼技能的效果',
      effects: ['+6% 战吼技能的效果'],
      requiredPoints: 15,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 2, col: 5, x: 808, y: 274 },
      connections: ['row3_col5'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Buff_64.webp'
    },

    // 第四行 (y=370) - 3, 6, 9, 12, 15, 18
    {
      id: 'row4_col1',
      name: '+7% 护甲值',
      type: 'notable',
      description: '+7% 护甲值',
      effects: ['+7% 护甲值'],
      requiredPoints: 3,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 3, col: 0, x: 272, y: 370 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Armor_64.webp'
    },
    {
      id: 'row4_col2',
      name: '+40% 从胸甲获得的防御值',
      type: 'small',
      description: '+40% 从胸甲获得的防御值',
      effects: ['+40% 从胸甲获得的防御值'],
      requiredPoints: 6,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 3, col: 1, x: 408, y: 370 },
      connections: ['row4_col1'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Armor_64.webp'
    },
    {
      id: 'row4_col3',
      name: '持盾时，+12% 伤害',
      type: 'notable',
      description: '持盾时，+12% 伤害，+4% 攻击格挡率',
      effects: ['持盾时，+12% 伤害', '持盾时，+4% 攻击格挡率'],
      requiredPoints: 9,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 3, col: 2, x: 544, y: 370 },
      connections: ['row4_col2'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Shield_64.webp'
    },
    {
      id: 'row4_col4',
      name: '+2% 元素抗性',
      type: 'small',
      description: '+2% 元素抗性，+2% 腐蚀抗性',
      effects: ['+2% 元素抗性', '+2% 腐蚀抗性'],
      requiredPoints: 12,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 3, col: 3, x: 672, y: 370 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Resist_64.webp'
    },
    {
      id: 'row4_col5',
      name: '每 24 点力量，+1% 护甲值',
      type: 'notable',
      description: '每 24 点力量，+1% 护甲值',
      effects: ['每 24 点力量，+1% 护甲值'],
      requiredPoints: 15,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 3, col: 4, x: 808, y: 370 },
      connections: ['row4_col4'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Armor_64.webp'
    },

    // 第五行 (y=466) - 0, 3, 6, 9, 18
    {
      id: 'row5_col1',
      name: '+7% 护甲值',
      type: 'small',
      description: '+7% 护甲值',
      effects: ['+7% 护甲值'],
      requiredPoints: 0,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 4, col: 0, x: 136, y: 466 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Armor_64.webp'
    },
    {
      id: 'row5_col2',
      name: '+8% 攻击格挡率',
      type: 'notable',
      description: '+8% 攻击格挡率',
      effects: ['+8% 攻击格挡率'],
      requiredPoints: 3,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 4, col: 1, x: 272, y: 466 },
      connections: ['row5_col1'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/Block_64.webp'
    },
    {
      id: 'row5_col3',
      name: '1.5% 生命返还',
      type: 'small',
      description: '1.5% 生命返还',
      effects: ['1.5% 生命返还'],
      requiredPoints: 6,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 4, col: 2, x: 408, y: 466 },
      connections: [],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/HP_64.webp'
    },
    {
      id: 'row5_col4',
      name: '+3% 生命返还',
      type: 'notable',
      description: '+3% 生命返还',
      effects: ['+3% 生命返还'],
      requiredPoints: 9,
      maxPoints: 3,
      currentPoints: 0,
      position: { row: 4, col: 3, x: 544, y: 466 },
      connections: ['row5_col3'],
      icon: 'https://cdn.tlidb.com/UI/Textures/Common/Icon/Silhouette/Talent/64/HP_64.webp'
    }
  ]
}

export const PROFESSION_TREES: ProfessionTalentTree[] = [
  THE_BRAVE_TREE
]

export { GRID_CONFIG, LEVELS }
