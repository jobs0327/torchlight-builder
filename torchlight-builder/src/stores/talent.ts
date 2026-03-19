import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { TalentNode, TalentTree, TalentPanel, GodType } from '@/types'
import { generateTalentPanels, GOD_NAMES } from '@/data/talents/meta/talentData'

export const useTalentStore = defineStore('talent', () => {
  const panels = ref<TalentPanel[]>([])
  const selectedNode = ref<TalentNode | null>(null)
  const totalPoints = ref(95)
  const allocatedNodes = ref<Set<string>>(new Set())

  const usedPoints = computed(() => allocatedNodes.value.size)
  const remainingPoints = computed(() => totalPoints.value - usedPoints.value)

  function initializePanels() {
    panels.value = generateTalentPanels()
    allocatedNodes.value.clear()
  }

  function allocateNode(nodeId: string): boolean {
    if (remainingPoints.value <= 0) return false
    
    const node = findNode(nodeId)
    if (!node || node.allocated) return false

    if (node.connections.length > 0 && usedPoints.value > 0) {
      const hasConnection = node.connections.some(connId => allocatedNodes.value.has(connId))
      if (!hasConnection) return false
    }

    allocatedNodes.value.add(nodeId)
    node.allocated = true
    return true
  }

  function deallocateNode(nodeId: string): boolean {
    const node = findNode(nodeId)
    if (!node || !node.allocated) return false

    for (const panel of panels.value) {
      for (const tree of panel.trees) {
        for (const n of tree.nodes) {
          if (n.connections.includes(nodeId) && n.allocated) {
            return false
          }
        }
      }
    }

    allocatedNodes.value.delete(nodeId)
    node.allocated = false
    return true
  }

  function toggleNode(nodeId: string) {
    const node = findNode(nodeId)
    if (!node) return

    if (node.allocated) {
      deallocateNode(nodeId)
    } else {
      allocateNode(nodeId)
    }
  }

  function findNode(nodeId: string): TalentNode | null {
    for (const panel of panels.value) {
      for (const tree of panel.trees) {
        const node = tree.nodes.find((n: TalentNode) => n.id === nodeId)
        if (node) return node
      }
    }
    return null
  }

  function selectNode(node: TalentNode | null) {
    selectedNode.value = node
  }

  function resetAllPoints() {
    allocatedNodes.value.clear()
    for (const panel of panels.value) {
      for (const tree of panel.trees) {
        for (const node of tree.nodes) {
          node.allocated = false
        }
      }
    }
    selectedNode.value = null
  }

  function getTreeByGodType(panelId: string, godType: GodType): TalentTree | null {
    const panel = panels.value.find((p: TalentPanel) => p.id === panelId)
    if (!panel) return null
    return panel.trees.find((t: TalentTree) => t.godType === godType) || null
  }

  function getAllocatedNodesByGod(godType: GodType): TalentNode[] {
    const nodes: TalentNode[] = []
    for (const panel of panels.value) {
      const tree = panel.trees.find((t: TalentTree) => t.godType === godType)
      if (tree) {
        nodes.push(...tree.nodes.filter((n: TalentNode) => n.allocated))
      }
    }
    return nodes
  }

  return {
    panels,
    selectedNode,
    totalPoints,
    allocatedNodes,
    usedPoints,
    remainingPoints,
    initializePanels,
    allocateNode,
    deallocateNode,
    toggleNode,
    selectNode,
    resetAllPoints,
    findNode,
    getTreeByGodType,
    getAllocatedNodesByGod
  }
})
