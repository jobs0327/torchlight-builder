import type { GodType, TalentNode, TalentTree, TalentPanel } from '@/types'
import { GOD_COLORS, GOD_NAMES } from '@/types'

export interface RawTalentData {
  name: string
  description: string
  effects: string[]
  position?: { x: number; y: number }
  connections?: string[]
}

export interface GodData {
  id: GodType
  name: string
  mainStat: string
  tags: string[]
  description: string
  talents: RawTalentData[]
}

export const GOD_DATA: Record<GodType, GodData> = {
  strength: {
    id: 'strength',
    name: '巨力之神',
    mainStat: '力量',
    tags: ['攻击'],
    description: '玛格努斯，无上天神之力',
    talents: []
  },
  dexterity: {
    id: 'dexterity',
    name: '狩猎之神',
    mainStat: '敏捷',
    tags: ['速度'],
    description: '汉娜，群星间的女猎手',
    talents: []
  },
  intelligence: {
    id: 'intelligence',
    name: '知识之神',
    mainStat: '智慧',
    tags: ['法术'],
    description: '伊丝拉菲尔，生灵与梦境的织者',
    talents: []
  },
  war: {
    id: 'war',
    name: '征战之神',
    mainStat: '力量、敏捷',
    tags: ['物理'],
    description: '雷尔夫，永恒战场的不败冠军',
    talents: []
  },
  trickery: {
    id: 'trickery',
    name: '欺诈之神',
    mainStat: '敏捷、智慧',
    tags: ['持续', '腐蚀'],
    description: '瓦里哀，役使谎言与幻象的奇术师',
    talents: []
  },
  machine: {
    id: 'machine',
    name: '机械之神',
    mainStat: '力量、智慧',
    tags: ['召唤', '哨卫'],
    description: '乌洛斯，不朽之躯的塑造者',
    talents: []
  }
}

export const PROFESSION_DATA = [
  { id: 'the_brave', name: '勇者', godType: 'strength' as GodType, tags: ['单手武器', '护甲'], description: '攻守均衡的战斗大师' },
  { id: 'onslaughter', name: '猛袭者', godType: 'strength' as GodType, tags: ['双手武器', '生命'], description: '英勇无畏，大刀阔斧' },
  { id: 'warlord', name: '督军', godType: 'strength' as GodType, tags: ['火焰', '范围'], description: '恪守骑士之道，惩戒一切邪恶' },
  { id: 'warrior', name: '斗士', godType: 'strength' as GodType, tags: ['生命'], description: '坚韧不屈，勇武之师' },
  { id: 'marksman', name: '神射手', godType: 'dexterity' as GodType, tags: ['投射物', '闪避'], description: '精通速度之力的狙击者' },
  { id: 'bladerunner', name: '刀锋行者', godType: 'dexterity' as GodType, tags: ['双持', '攻击速度'], description: '闪耀于阴影中的寒刃' },
  { id: 'druid', name: '德鲁伊', godType: 'dexterity' as GodType, tags: ['施法速度', '返还'], description: '致力于守护自然平衡的隐居者' },
  { id: 'assassin', name: '刺客', godType: 'dexterity' as GodType, tags: ['闪电'], description: '无声无息，动如闪电' },
  { id: 'magister', name: '魔导师', godType: 'intelligence' as GodType, tags: ['法术', '护盾'], description: '深究世界本源的魔法导师' },
  { id: 'arcanist', name: '秘术师', godType: 'intelligence' as GodType, tags: ['法术', '魔力'], description: '醉心于隐秘知识的神秘主义者' },
  { id: 'elementalist', name: '元素师', godType: 'intelligence' as GodType, tags: ['引导', '元素'], description: '引导操纵自然能量，孕育催化元素之力' },
  { id: 'prophet', name: '先知', godType: 'intelligence' as GodType, tags: ['冰冷'], description: '洞悉的命运之眼' },
  { id: 'shadowdancer', name: '影舞者', godType: 'war' as GodType, tags: ['物理', '触发'], description: '从阴影中降临，于无声处逝去' },
  { id: 'ronin', name: '神行武士', godType: 'war' as GodType, tags: ['近战', '格挡'], description: '行侠仗义，行踪飘忽' },
  { id: 'ranger', name: '游侠', godType: 'war' as GodType, tags: ['暴击', '距离'], description: '专注强力一击的渗透专家，兼顾强大的生存技巧' },
  { id: 'sentinel', name: '铁卫', godType: 'war' as GodType, tags: ['格挡', '盾牌'], description: '坚不可摧的忠诚壁垒' },
  { id: 'shadowmaster', name: '驭影者', godType: 'trickery' as GodType, tags: ['腐蚀', '封印'], description: '着迷于地下世界景象的艺术家' },
  { id: 'psychic', name: '异能者', godType: 'trickery' as GodType, tags: ['持续'], description: '背弃常识的狂人，于禁忌中激发超人之力' },
  { id: 'warlock', name: '暗影术士', godType: 'trickery' as GodType, tags: ['异常', '负面效果'], description: '信仰黑暗之力的魔法大师' },
  { id: 'lich', name: '巫妖', godType: 'trickery' as GodType, tags: ['技能', '封印'], description: '生灵与亡者的桥梁' },
  { id: 'machinist', name: '机械师', godType: 'machine' as GodType, tags: ['智械', '召唤'], description: '科技就是力量' },
  { id: 'steel_vanguard', name: '钢铁先锋', godType: 'machine' as GodType, tags: ['增益效果', '抗性'], description: '重兵在握，无往不利' },
  { id: 'alchemist', name: '炼金术士', godType: 'machine' as GodType, tags: ['魔灵', '召唤'], description: '试剂中蕴藏的一半是危险，另一半是希望' },
  { id: 'artisan', name: '巧匠', godType: 'machine' as GodType, tags: ['哨卫', '屏障'], description: '巧手造物的巨匠' }
]

function generateTalentNodes(godType: GodType): TalentNode[] {
  const nodes: TalentNode[] = []
  const centerX = 400
  const centerY = 400
  const color = GOD_COLORS[godType]
  
  const keystoneEffects: Record<GodType, string[]> = {
    strength: ['+25% 物理伤害', '+15% 攻击速度', '攻击技能额外 +20% 伤害'],
    dexterity: ['+20% 攻击速度', '+25% 闪避值', '投射物穿透 +1'],
    intelligence: ['+25% 法术伤害', '+20% 最大魔力', '法术技能额外 +15% 伤害'],
    war: ['+20% 物理伤害', '+15% 攻击速度', '近战攻击额外 +25% 伤害'],
    trickery: ['+25% 腐蚀伤害', '+20% 持续伤害', '异常状态持续时间 +30%'],
    machine: ['+20% 召唤物伤害', '+25% 哨卫伤害', '召唤物最大数量 +1']
  }

  const nodeEffects: Record<GodType, string[][]> = {
    strength: [
      ['+10% 物理伤害', '+5% 攻击速度'],
      ['+15% 最大生命', '+5% 力量'],
      ['+8% 近战伤害', '近战攻击范围 +1'],
      ['+10% 暴击率', '+20% 暴击伤害'],
      ['+12% 攻击速度', '攻击技能魔力消耗 -10%'],
      ['+20% 物理伤害', '物理穿透 +5%'],
      ['+10% 最大生命', '+5% 生命回复'],
      ['+15% 伤害', '攻击击中回复生命 +5']
    ],
    dexterity: [
      ['+10% 攻击速度', '+5% 敏捷'],
      ['+15% 闪避值', '+5% 移动速度'],
      ['+10% 投射物伤害', '投射物速度 +20%'],
      ['+8% 暴击率', '+15% 暴击伤害'],
      ['+12% 攻击速度', '闪避 +10%'],
      ['+15% 投射物伤害', '投射物穿透 +1'],
      ['+10% 移动速度', '闪避值 +10%'],
      ['+12% 攻击伤害', '攻击技能魔力消耗 -10%']
    ],
    intelligence: [
      ['+10% 法术伤害', '+5% 智慧'],
      ['+15% 最大魔力', '+5% 魔力回复'],
      ['+12% 元素伤害', '元素穿透 +5%'],
      ['+10% 施法速度', '法术技能魔力消耗 -10%'],
      ['+15% 最大护盾', '+5% 护盾回复'],
      ['+12% 法术伤害', '法术范围 +10%'],
      ['+10% 冰冷伤害', '冰冷穿透 +5%'],
      ['+10% 火焰伤害', '火焰穿透 +5%']
    ],
    war: [
      ['+10% 物理伤害', '+5% 力量'],
      ['+10% 攻击速度', '+5% 敏捷'],
      ['+15% 近战伤害', '近战范围 +1'],
      ['+12% 暴击率', '+20% 暴击伤害'],
      ['+15% 最大生命', '+5% 生命回复'],
      ['+10% 物理伤害', '物理穿透 +5%'],
      ['+12% 攻击速度', '近战伤害 +10%'],
      ['+15% 伤害', '暴击率 +8%']
    ],
    trickery: [
      ['+10% 腐蚀伤害', '+5% 敏捷'],
      ['+12% 持续伤害', '+5% 智慧'],
      ['+15% 异常伤害', '异常持续时间 +15%'],
      ['+10% 施法速度', '腐蚀穿透 +5%'],
      ['+12% 腐蚀伤害', '腐蚀效果 +10%'],
      ['+15% 持续伤害', '持续技能效果 +10%'],
      ['+10% 异常几率', '异常效果 +10%'],
      ['+12% 伤害', '技能持续时间 +15%']
    ],
    machine: [
      ['+10% 召唤物伤害', '+5% 力量'],
      ['+12% 哨卫伤害', '+5% 智慧'],
      ['+15% 召唤物生命', '召唤物数量 +1'],
      ['+10% 哨卫攻击速度', '哨卫数量 +1'],
      ['+12% 召唤物伤害', '召唤物持续时间 +20%'],
      ['+15% 哨卫伤害', '哨卫持续时间 +20%'],
      ['+10% 召唤物速度', '召唤物范围 +15%'],
      ['+12% 哨卫范围', '哨卫伤害 +10%']
    ]
  }

  nodes.push({
    id: `${godType}-keystone`,
    name: `${GOD_NAMES[godType]}核心`,
    description: GOD_DATA[godType].description,
    position: { x: centerX, y: centerY },
    type: 'keystone',
    godType,
    effects: keystoneEffects[godType].map((e, i) => ({
      type: 'modifier' as const,
      description: e
    })),
    connections: [],
    allocated: false
  })

  const innerRadius = 150
  const effects = nodeEffects[godType]
  
  for (let i = 0; i < 8; i++) {
    const angle = (i / 8) * Math.PI * 2 - Math.PI / 2
    const x = centerX + Math.cos(angle) * innerRadius
    const y = centerY + Math.sin(angle) * innerRadius
    const nodeEffect = effects[i]

    nodes.push({
      id: `${godType}-notable-${i}`,
      name: `${['力量', '敏捷', '智慧', '战争', '诡诈', '机械'][Math.floor(i / 2) % 6]}天赋 ${i + 1}`,
      description: nodeEffect.join('，'),
      position: { x, y },
      type: 'notable',
      godType,
      effects: nodeEffect.map(e => ({
        type: 'stat' as const,
        description: e
      })),
      connections: [`${godType}-keystone`],
      allocated: false
    })
  }

  const outerRadius = 250
  for (let i = 0; i < 16; i++) {
    const angle = (i / 16) * Math.PI * 2 - Math.PI / 2
    const x = centerX + Math.cos(angle) * outerRadius
    const y = centerY + Math.sin(angle) * outerRadius
    const effectIndex = i % 8
    const effect = effects[effectIndex]

    nodes.push({
      id: `${godType}-normal-${i}`,
      name: `天赋节点 ${i + 1}`,
      description: effect[0],
      position: { x, y },
      type: 'normal',
      godType,
      effects: [{
        type: 'stat' as const,
        description: effect[0]
      }],
      connections: [`${godType}-notable-${Math.floor(i / 2)}`],
      allocated: false
    })
  }

  return nodes
}

export function generateTalentPanels(): TalentPanel[] {
  const godTypes: GodType[] = ['strength', 'dexterity', 'intelligence', 'war', 'trickery', 'machine']
  
  return [
    {
      id: 'panel-1',
      name: '天赋盘 1',
      position: 1,
      trees: godTypes.map(godType => ({
        id: `tree-${godType}-1`,
        name: GOD_NAMES[godType],
        godType,
        description: GOD_DATA[godType].description,
        nodes: generateTalentNodes(godType),
        totalPoints: 25,
        allocatedPoints: 0
      }))
    },
    {
      id: 'panel-2',
      name: '天赋盘 2',
      position: 2,
      trees: godTypes.map(godType => ({
        id: `tree-${godType}-2`,
        name: GOD_NAMES[godType],
        godType,
        description: GOD_DATA[godType].description,
        nodes: generateTalentNodes(godType),
        totalPoints: 25,
        allocatedPoints: 0
      }))
    }
  ]
}

export function getProfessionsByGod(godType: GodType) {
  return PROFESSION_DATA.filter(p => p.godType === godType)
}

export { GOD_COLORS, GOD_NAMES }

