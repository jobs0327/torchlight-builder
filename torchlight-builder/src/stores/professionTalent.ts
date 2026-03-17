import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ProfessionTalentTree, ProfessionTalentNode } from '@/data/professionTalentData'
import { THE_BRAVE_TREE } from '@/data/professionTalentData'

export const useProfessionTalentStore = defineStore('professionTalent', () => {
  const trees = ref<ProfessionTalentTree[]>([JSON.parse(JSON.stringify(THE_BRAVE_TREE))])
  const activeTreeId = ref<string>('the_brave')

  const activeTree = computed(() => 
    trees.value.find(t => t.id === activeTreeId.value) || null
  )

  const totalAllocatedPoints = computed(() => 
    trees.value.reduce((sum, tree) => sum + tree.allocatedPoints, 0)
  )

  function allocateNode(nodeId: string): boolean {
    const tree = activeTree.value
    if (!tree) return false

    const node = tree.nodes.find(n => n.id === nodeId)
    if (!node) return false

    if (tree.allocatedPoints < node.requiredPoints) return false

    const hasAllocatedParent = node.connections.length === 0 || 
      node.connections.some(parentId => {
        const parentNode = tree.nodes.find(n => n.id === parentId)
        return parentNode && parentNode.currentPoints > 0
      })
    
    if (!hasAllocatedParent) return false

    if (node.currentPoints >= node.maxPoints) return false

    node.currentPoints++
    tree.allocatedPoints++
    return true
  }

  function deallocateNode(nodeId: string): boolean {
    const tree = activeTree.value
    if (!tree) return false

    const node = tree.nodes.find(n => n.id === nodeId)
    if (!node || node.currentPoints <= 0) return false

    const hasAllocatedChildren = tree.nodes.some(n => 
      n.connections.includes(nodeId) && n.currentPoints > 0
    )
    if (hasAllocatedChildren && node.currentPoints === 1) return false

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
    tree.allocatedPoints = 0
  }

  function setActiveTree(treeId: string) {
    activeTreeId.value = treeId
  }

  function getAllocatedEffects(): string[] {
    const effects: string[] = []
    for (const tree of trees.value) {
      for (const node of tree.nodes) {
        if (node.currentPoints > 0) {
          effects.push(...node.effects)
        }
      }
    }
    return effects
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
