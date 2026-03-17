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

export { GRID_CONFIG, LEVELS }
