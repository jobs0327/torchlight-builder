import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ProfessionTalentTree, ProfessionTalentNode } from '@/data/professionTalentData'
import professionTreesJson from '@/data/profession_trees.json'

function stripHtml(text: string): string {
  return text.replace(/<[^>]*>/g, '')
}

export const useProfessionTalentStore = defineStore('professionTalent', () => {
  const trees = ref<ProfessionTalentTree[]>(
    (professionTreesJson as ProfessionTalentTree[]).map(tree =>
      JSON.parse(JSON.stringify(tree)) as ProfessionTalentTree
    )
  )
  const activeTreeId = ref<string>(trees.value[0]?.id ?? '')

  const activeTree = computed(() => 
    trees.value.find(t => t.id === activeTreeId.value) || null
  )

  const totalAllocatedPoints = computed(() => 
    trees.value.reduce((sum, tree) => sum + tree.allocatedPoints, 0)
  )

  function allocateNode(nodeId: string): boolean {
    const tree = activeTree.value
    if (!tree) return false

    let node: ProfessionTalentNode | undefined =
      tree.nodes.find(n => n.id === nodeId) ||
      tree.coreTalents.find(n => n.id === nodeId)
    if (!node) return false

    // 核心天赋：根据自身 requiredPoints 与天赋树总加点数联动，且全局单选
    if (node.id.startsWith('core_')) {
      if (tree.allocatedPoints < node.requiredPoints) return false

      // 如果已经选中过其他核心天赋，则先取消之前的核心点数
      for (const core of tree.coreTalents) {
        if (core.id !== node.id && core.currentPoints > 0) {
          tree.allocatedPoints -= core.currentPoints
          core.currentPoints = 0
        }
      }
    }

    // 传奇天赋永远只能加 1 点（即使数据里写的是 3）
    const maxPoints = node.type === 'legendary' ? 1 : node.maxPoints

    // 再做一层防御性校验：所有前置节点必须点满
    if ('position' in node) {
      const parents = tree.nodes.filter(
        n =>
          node.connections.includes(n.id) &&
          (n.position.col ?? 0) < (node.position.col ?? 0)
      )
      if (
        parents.length > 0 &&
        !parents.every(p => p.currentPoints >= (p.type === 'legendary' ? 1 : p.maxPoints))
      ) {
        return false
      }
    }

    if (node.currentPoints >= maxPoints) return false

    node.currentPoints++
    tree.allocatedPoints++
    return true
  }

  function deallocateNode(nodeId: string): boolean {
    const tree = activeTree.value
    if (!tree) return false

    let node: ProfessionTalentNode | undefined =
      tree.nodes.find(n => n.id === nodeId) ||
      tree.coreTalents.find(n => n.id === nodeId)
    if (!node || node.currentPoints <= 0) return false

    const hasAllocatedChildren = tree.nodes.some(n =>
      n.connections.includes(nodeId) &&
      n.currentPoints > 0 &&
      // 只把「在纵向后面的」节点视为后续节点，避免双向连接导致互相锁死
      n.position.col > (node.position.col ?? 0)
    )
    // 规则：当前节点作为「前置节点」时，只要后续有已分配点的节点，就完全不能取消加点
    if (hasAllocatedChildren) return false

    node.currentPoints--
    tree.allocatedPoints--
    return true
  }

  function resetTree(treeId?: string) {
    const tree = treeId 
      ? trees.value.find(t => t.id === treeId) 
      : activeTree.value
    
    if (!tree) return

    for (const node of tree.nodes) {
      node.currentPoints = 0
    }
    for (const core of tree.coreTalents) {
      core.currentPoints = 0
    }
    tree.allocatedPoints = 0
  }

  function setActiveTree(treeId: string) {
    activeTreeId.value = treeId
  }

  function getAllocatedEffects(): string[] {
    const effectCounter = new Map<string, number>()

    // 数值汇总表：键是规范化后的统计名（例如 "% 攻击伤害"、"护甲值"），值是累加数值
    const numericTotals = new Map<string, number>()

    function tryAccumulateNumeric(clean: string): boolean {
      // 通用规则：匹配「前缀 + 数值(+可选%) + 单位」形式，例如：
      // "+9% 攻击伤害"
      // "持单手武器时， +18% 攻击伤害"
      // "+450 护甲值"
      const m = clean.match(
        /^(.*?)([+-]?\d+(?:\.\d+)?)(\s*%?)(.*)$/
      )
      if (!m) return false

      const prefix = m[1].trim()
      const numStr = m[2]
      const percentPart = m[3].trim()
      const suffix = m[4].trim()

      const val = Number(numStr)
      if (Number.isNaN(val)) return false

      const isPercent = percentPart === '%'
      // 归一化 label：保留前缀和单位，数值和 % 不再放在 label 里，便于后续重建
      const labelParts: string[] = []
      if (prefix) labelParts.push(prefix)
      if (suffix) labelParts.push(suffix)
      const label = labelParts.join(' ').trim() || clean

      const key = `${isPercent ? 'P' : 'N'}|${label}`
      numericTotals.set(key, (numericTotals.get(key) ?? 0) + val)
      return true
    }

    for (const tree of trees.value) {
      for (const node of tree.nodes) {
        if (node.currentPoints > 0) {
          for (let i = 0; i < node.currentPoints; i++) {
            for (const effect of node.effects) {
              const clean = stripHtml(effect)
              if (!clean) continue

              // 尝试做数值汇总（攻击伤害、暴击值、护甲值等）
              if (tryAccumulateNumeric(clean)) continue

              effectCounter.set(clean, (effectCounter.get(clean) ?? 0) + 1)
            }
          }
        }
      }
      for (const core of tree.coreTalents) {
        if (core.currentPoints > 0) {
          for (let i = 0; i < core.currentPoints; i++) {
            for (const effect of core.effects) {
              const clean = stripHtml(effect)
              if (!clean) continue

              if (tryAccumulateNumeric(clean)) continue

              effectCounter.set(clean, (effectCounter.get(clean) ?? 0) + 1)
            }
          }
        }
      }
    }

    // 合并相同效果：相同文本只显示一条，后缀标注次数，如「+9% 攻击伤害 x3」
    const merged: string[] = []

    // 先加入所有汇总好的数值效果
    for (const [key, total] of numericTotals.entries()) {
      const [kind, label] = key.split('|', 2)
      const isPercent = kind === 'P'
      const displayValue = total
      const sign = displayValue > 0 ? '+' : ''

      if (isPercent) {
        // 百分比：重建为「前缀 + 数值% 单位」
        merged.push(`${sign}${displayValue}% ${label}`)
      } else {
        // 非百分比：重建为「前缀 + 数值 单位」
        merged.push(`${sign}${displayValue} ${label}`)
      }
    }

    for (const [text, count] of effectCounter.entries()) {
      merged.push(count > 1 ? `${text} x${count}` : text)
    }

    // 为了展示稳定性，对结果做一下排序（按文本）
    merged.sort((a, b) => a.localeCompare(b, 'zh-CN'))

    return merged
  }

  return {
    trees,
    activeTreeId,
    activeTree,
    totalAllocatedPoints,
    allocateNode,
    deallocateNode,
    resetTree,
    setActiveTree,
    getAllocatedEffects
  }
})
