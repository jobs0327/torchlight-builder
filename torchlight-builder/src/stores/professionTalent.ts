import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { ProfessionTalentTree, ProfessionTalentNode } from '@/data/talents/meta/professionTalentData'
import professionTreesJson from '@/data/talents/profession_trees.json'
import { LEVELS } from '@/data/talents/meta/professionTalentData'
import { GOD_NAMES } from '@/types'

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
  // 总览里职业面板的“选中顺序”（仅职业面板，不含神格面板）
  const selectedProfessionOrder = ref<string[]>([])
  // 总览模块的“选中高亮”状态，保存到 trees 数据里（运行时内存态）
  for (const t of trees.value) {
    if (typeof t.isSelected !== 'boolean') t.isSelected = false
    // 兼容旧数据：若没带 isGodRoot，则通过「名称是否等于神格名」推导
    if (typeof (t as any).isGodRoot !== 'boolean') {
      ;(t as any).isGodRoot = t.name === GOD_NAMES[t.godType]
    }
  }
  if (activeTreeId.value) {
    const initial = trees.value.find(t => t.id === activeTreeId.value)
    if (initial) initial.isSelected = true
  }

  // 初始化职业面板选中顺序（基于当前 isSelected 的顺序，不保证历史顺序，仅用于首屏一致性）
  selectedProfessionOrder.value = trees.value
    .filter(t => t.isSelected && !t.isGodRoot)
    .map(t => t.id)

  const activeTree = computed(() => 
    trees.value.find(t => t.id === activeTreeId.value) || null
  )

  const toastMessage = ref<string>('')
  let toastTimer: number | null = null

  function pushToast(message: string, durationMs = 2200) {
    toastMessage.value = message
    if (toastTimer) window.clearTimeout(toastTimer)
    toastTimer = window.setTimeout(() => {
      toastMessage.value = ''
      toastTimer = null
    }, durationMs)
  }

  /** 与天赋树 UI 层级刻度一致：列索引 → 「第 N 层」（N 为总点数门槛） */
  function layerLabelForCol(col: number): string {
    const idx = Math.min(Math.max(col, 0), LEVELS.length - 1)
    return `第 ${LEVELS[idx]} 层`
  }

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

    const isCore = node.id.startsWith('core_')

    // 核心天赋：根据自身 requiredPoints 与天赋树总加点数联动
    if (node.id.startsWith('core_')) {
      if (tree.allocatedPoints < node.requiredPoints) return false

      // 核心天赋选择规则：
      // - 职业页通常只有同一档 requiredPoints（如 24），等价于单选
      // - 神格页会出现两档（如 12 / 24），应允许「每一档各选一个」
      // 因此仅在同一档 requiredPoints 内互斥。
      for (const core of tree.coreTalents) {
        if (
          core.id !== node.id &&
          core.currentPoints > 0 &&
          core.requiredPoints === node.requiredPoints
        ) {
          tree.allocatedPoints -= core.currentPoints
          core.currentPoints = 0
        }
      }
    }

    // 传奇天赋永远只能加 1 点（即使数据里写的是 3）
    const maxPoints = node.type === 'legendary' ? 1 : node.maxPoints

    // 再做一层防御性校验：所有前置节点必须点满
    if (!isCore && 'position' in node) {
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

    // 注意：神格树内的普通节点加点不应依赖是否已选择核心天赋；
    // 核心天赋本身受 requiredPoints 门槛控制即可，避免形成“先选核心/先加点”的死锁。

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

    const myCol = node.position?.col ?? 0
    const blockers = tree.nodes.filter(
      n =>
        n.connections.includes(nodeId) &&
        n.currentPoints > 0 &&
        // 只把「在纵向后面的」节点视为后续节点，避免双向连接导致互相锁死
        (n.position?.col ?? 0) > myCol
    )
    // 规则：当前节点作为「前置」时，只要更右侧仍有已加点的依赖节点，就不能撤回本节点
    if (blockers.length > 0) {
      const sorted = [...blockers].sort(
        (a, b) => (a.position?.col ?? 0) - (b.position?.col ?? 0)
      )
      const maxShow = 4
      const parts = sorted.slice(0, maxShow).map(n => {
        const layer = layerLabelForCol(n.position?.col ?? 0)
        return `${layer}「${n.name}」`
      })
      const more =
        sorted.length > maxShow ? ` 等共 ${sorted.length} 个` : ''
      pushToast(
        `无法取消「${node.name}」：更后层仍有天赋以其为前置且已加点。请先撤回：${parts.join('、')}${more}。`,
        4500
      )
      return false
    }

    // 神格树退点：不额外施加“必须保留某列至少 1 个”等限制（按用户最新需求）

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

  type TreeSelectResult = 'SELECTED' | 'DESELECTED' | 'NEED_CONFIRM_CLEAR'

  function setActiveTree(treeId: string): TreeSelectResult | void {
    const t = trees.value.find(x => x.id === treeId)
    if (!t) return

    // 总览交互调整：点击面板只负责“选中/切换右侧展示”，不再通过再次点击来取消选中。
    // 取消选中由右侧 X 按钮触发（见 deselectTree）。
    const isAlreadySelected = !!t.isSelected
    if (isAlreadySelected) {
      activeTreeId.value = treeId
      return 'SELECTED'
    }

    // 点击未选中面板：选中（不影响其他已选中）
    // 规则 A：6 个神格天赋面板（isGodRoot）互斥，只能选 1 个
    // 总览限制：若当前已选中的神格天赋下已有职业天赋加点，则不允许在总览里切换到其他神格
    if (t.isGodRoot) {
      const currentSelectedGod = trees.value.find(x => x.isSelected && x.isGodRoot)
      if (currentSelectedGod && (currentSelectedGod.allocatedPoints ?? 0) > 0) {
        pushToast('当前神格天赋下已有职业天赋选择，无法切换神格')
        return
      }
      for (const tree of trees.value) {
        if (tree.isGodRoot) tree.isSelected = false
      }
      t.isSelected = true
      activeTreeId.value = treeId
      return 'SELECTED'
    }

    // 以下均为职业面板规则（不含神格面板）
    const selectedGod = trees.value.find(x => x.isSelected && x.isGodRoot) || null
    const selectedProfessionCount = trees.value.reduce(
      (sum, tree) => sum + (tree.isSelected && !tree.isGodRoot ? 1 : 0),
      0
    )

    // 规则 B：最多同时选中 3 个职业天赋面板
    if (selectedProfessionCount >= 3) {
      pushToast('最多只能选择三个职业天赋')
      return
    }

    // 规则 C：当已选中一个神格天赋后，第一个职业天赋必须来自当前神格（同 godType）
    if (selectedProfessionCount === 0) {
      if (!selectedGod) {
        pushToast('请先选择一个神格天赋')
        return
      }
      if (t.godType !== selectedGod.godType) {
        pushToast('第一个职业天赋必须从当前神格天赋下选择')
        return
      }
    }

    t.isSelected = true
    selectedProfessionOrder.value = [...selectedProfessionOrder.value, treeId]
    activeTreeId.value = treeId
    return 'SELECTED'
  }

  function deselectTree(treeId: string): TreeSelectResult | void {
    const t = trees.value.find(x => x.id === treeId)
    if (!t) return
    if (!t.isSelected) return

    if ((t.allocatedPoints ?? 0) > 0) {
      // 通过返回特殊值让调用方弹出确认框
      // 注意：此处不要改动 isSelected/activeTreeId，用户点“取消”时应保持高亮不变
      return 'NEED_CONFIRM_CLEAR'
    }

    t.isSelected = false
    if (!t.isGodRoot) {
      selectedProfessionOrder.value = selectedProfessionOrder.value.filter(id => id !== treeId)
    }
    if (activeTreeId.value === treeId) {
      activeTreeId.value = ''
    }
    return 'DESELECTED'
  }

  /**
   * 从 build 快照恢复职业天赋树（localStorage 持久化后刷新页面时调用）。
   * 仅合并与存档中 id 对应的节点点数与选中态，避免数据结构升级时整页崩溃。
   */
  function applyFromPersistedBuild(talent: {
    professionTreesFull?: unknown
  }) {
    const full = talent.professionTreesFull
    if (!Array.isArray(full)) return
    for (const st of full as ProfessionTalentTree[]) {
      if (!st || typeof st.id !== 'string') continue
      const live = trees.value.find(x => x.id === st.id)
      if (!live) continue
      live.isSelected = !!st.isSelected
      live.allocatedPoints = typeof st.allocatedPoints === 'number' ? st.allocatedPoints : 0
      for (const n of st.nodes ?? []) {
        const ln = live.nodes.find(x => x.id === n.id)
        if (ln && typeof n.currentPoints === 'number') ln.currentPoints = n.currentPoints
      }
      for (const c of st.coreTalents ?? []) {
        const lc = live.coreTalents.find(x => x.id === c.id)
        if (lc && typeof c.currentPoints === 'number') lc.currentPoints = c.currentPoints
      }
    }
    selectedProfessionOrder.value = trees.value
      .filter(t => t.isSelected && !t.isGodRoot)
      .map(t => t.id)
    const firstSel = trees.value.find(t => t.isSelected)
    if (firstSel) activeTreeId.value = firstSel.id
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

  /**
   * 已加点天赋/核心的效果原文列表（每点每条各出现一次，不做数值合并与「 xN」后缀）。
   * 供伤害转化等需按条解析的模块使用，避免 getAllocatedEffects 把「5% … 转化为 …」误并入其它统计。
   */
  function getAllocatedEffectRawLines(): string[] {
    const out: string[] = []
    for (const tree of trees.value) {
      for (const node of tree.nodes) {
        if (node.currentPoints <= 0) continue
        for (let i = 0; i < node.currentPoints; i++) {
          for (const effect of node.effects) {
            const clean = stripHtml(effect).trim()
            if (clean) out.push(clean)
          }
        }
      }
      for (const core of tree.coreTalents) {
        if (core.currentPoints <= 0) continue
        for (let i = 0; i < core.currentPoints; i++) {
          for (const effect of core.effects) {
            const clean = stripHtml(effect).trim()
            if (clean) out.push(clean)
          }
        }
      }
    }
    return out
  }

  return {
    trees,
    activeTreeId,
    activeTree,
    totalAllocatedPoints,
    toastMessage,
    selectedProfessionOrder,
    applyFromPersistedBuild,
    allocateNode,
    deallocateNode,
    resetTree,
    setActiveTree,
    deselectTree,
    getAllocatedEffects,
    getAllocatedEffectRawLines
  }
})
