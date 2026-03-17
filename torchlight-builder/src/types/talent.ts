export type GodType = 'strength' | 'dexterity' | 'intelligence' | 'war' | 'trickery' | 'machine'

export interface TalentNode {
  id: string
  name: string
  description: string
  icon?: string
  position: {
    x: number
    y: number
  }
  type: 'normal' | 'notable' | 'keystone'
  godType?: GodType
  effects: TalentEffect[]
  requirements?: {
    level?: number
    nodes?: string[]
  }
  connections: string[]
  allocated: boolean
}

export interface TalentEffect {
  type: 'stat' | 'modifier' | 'special'
  stat?: string
  value?: number
  modifier?: string
  description: string
}

export interface TalentTree {
  id: string
  name: string
  godType: GodType
  description: string
  nodes: TalentNode[]
  totalPoints: number
  allocatedPoints: number
}

export interface TalentPanel {
  id: string
  name: string
  position: number
  trees: TalentTree[]
}

export interface TalentState {
  panels: TalentPanel[]
  totalPoints: number
  usedPoints: number
  allocatedNodes: Set<string>
}

export const GOD_COLORS: Record<GodType, string> = {
  strength: '#e94560',
  dexterity: '#4ade80',
  intelligence: '#60a5fa',
  war: '#f97316',
  trickery: '#a855f7',
  machine: '#fbbf24'
}

export const GOD_NAMES: Record<GodType, string> = {
  strength: '巨力之神',
  dexterity: '狩猎之神',
  intelligence: '知识之神',
  war: '征战之神',
  trickery: '欺诈之神',
  machine: '机械之神'
}
