<template>
  <div class="profession-tree-container" ref="containerRef">
    <div class="tree-header">
      <div class="profession-info">
        <h2 class="profession-name">{{ tree.name }}</h2>
        <div class="profession-tags">
          <span v-for="tag in tree.tags" :key="tag" class="tag">{{ tag }}</span>
        </div>
      </div>
      <div class="points-info">
        <span class="points-text">{{ tree.allocatedPoints }} / {{ tree.totalPoints }} pts</span>
        <button class="close-btn" @click="$emit('close')" title="取消选中">×</button>
        <button class="reset-btn" @click="resetTree">重置</button>
      </div>
    </div>

    <div class="tree-viewport" ref="viewportRef">
      <!-- 核心天赋区域 -->
      <div class="core-talents-section" :style="{ height: coreSectionHeight + 'px' }">
        <div class="core-talents-container">
          <template v-for="(node, idx) in sortedCoreTalents" :key="node.id">
            <div 
              :class="[
                'core-talent-node',
                {
                  allocated: node.currentPoints > 0,
                  locked: tree.allocatedPoints < node.requiredPoints,
                  hovered: hoveredNode?.id === node.id
                }
              ]"
              @click.stop="onNodeClick(node)"
              @contextmenu.stop="onNodeRightClick(node, $event)"
              @mouseenter="onNodeHover(node, $event)"
              @mouseleave="onNodeLeave"
            >
              <div class="core-talent-icon">
                <div class="core-talent-background" :style="{ backgroundColor: getNodeBackgroundColor(node) }"></div>
                <div class="core-talent-ring" :style="{ borderColor: getNodeColor(node) }">
                  <span v-if="node.currentPoints > 0" class="core-talent-check">✓</span>
                  <div v-else class="core-talent-icon-container">
                    <img 
                      :src="node.icon || getTalentIcon(node)" 
                      :alt="node.name"
                      class="core-talent-icon-image"
                    />
                  </div>
                </div>
              </div>
              <div class="core-talent-info">
                <div class="core-talent-name">{{ node.name }}</div>
                <div class="core-talent-points">需要 {{ node.requiredPoints }} 点</div>
              </div>
            </div>

            <div
              v-if="idx === 2 && sortedCoreTalents.length >= 6"
              class="core-talents-divider"
              aria-hidden="true"
            />
          </template>
        </div>
      </div>

      <div 
        class="tree-content" 
        :style="contentStyle" 
        @mousedown="startDrag" 
        @mousemove="onDrag" 
        @mouseup="endDrag" 
        @mouseleave="endDrag"
      >
        <!-- 背景装饰 -->
        <div class="background-decor">
          <div class="decor-circle" style="top: 20%; left: 10%;"></div>
          <div class="decor-circle" style="top: 60%; right: 10%;"></div>
          <div class="decor-circle" style="bottom: 20%; left: 20%;"></div>
        </div>

        <!-- 层级指示器 -->
        <div class="level-indicators">
          <div class="level-line"></div>
          <div 
            v-for="(level, index) in LEVELS" 
            :key="level"
            class="level-indicator"
            :style="getLevelIndicatorStyle(level, index)"
          >
            <span class="level-number">{{ level }}</span>
          </div>
        </div>

        <!-- 连接线 -->
        <svg class="connections-svg" :viewBox="`0 0 ${svgWidth} ${svgHeight}`">
          <g class="connections">
            <path
              v-for="conn in connections"
              :key="conn.id"
              :d="conn.path"
              :class="['connection-path', { active: conn.active }]"
            />
          </g>
        </svg>

        <!-- 天赋节点 -->
        <div 
          v-for="node in tree.nodes" 
          :key="node.id"
          :class="['talent-node-wrapper', node.type, { allocated: node.currentPoints > 0, locked: isLocked(node), hovered: hoveredNode?.id === node.id }]"
          :style="getNodeStyle(node)"
          @click.stop="onNodeClick(node)"
          @contextmenu.stop="onNodeRightClick(node, $event)"
          @mouseenter="onNodeHover(node, $event)"
          @mouseleave="onNodeLeave"
        >
          <div class="node-icon">
            <div class="node-background" :style="{ backgroundColor: getNodeBackgroundColor(node) }"></div>
            <div class="node-ring" :style="{ borderColor: getNodeColor(node) }">
              <span
                v-if="node.currentPoints > 0"
                class="node-points"
              >
                {{ node.currentPoints }}/{{ getDisplayMaxPoints(node) }}
              </span>
              <div v-else class="node-icon-container">
                <img 
                  :src="getTalentIcon(node)" 
                  :alt="node.name"
                  class="node-icon-image"
                />
              </div>
            </div>
          </div>
          <div class="node-name">{{ getDisplayName(node) }}</div>
        </div>
      </div>
    </div>

    <div v-if="hoveredNode" class="node-tooltip" :style="tooltipStyle">
      <div class="tooltip-header">
        <span
          :class="['tooltip-type', hoveredNode.id?.startsWith('core_') ? 'core' : hoveredNode.type]"
        >
          {{ getNodeTypeName(hoveredNode.type, hoveredNode.id) }}
        </span>
        <span class="tooltip-name">{{ getDisplayName(hoveredNode) }}</span>
      </div>
      <div class="tooltip-effects">
        <p v-for="(effect, index) in hoveredNode.effects" :key="index" class="effect-line">
          {{ effect }}
        </p>
      </div>
      <div
        v-if="hoveredNode.requiredPoints > 0 && !hoveredNode.id?.startsWith('core_')"
        class="tooltip-requirement"
      >
        需要 {{ hoveredNode.requiredPoints }} 点已分配
      </div>
      <div class="tooltip-points">
        <span class="points-label">可分配点数:</span>
        <span class="points-value">{{ getDisplayMaxPoints(hoveredNode) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { ProfessionTalentTree, ProfessionTalentNode } from '@/data/talents/meta/professionTalentData'
import { GRID_CONFIG, LEVELS } from '@/data/talents/meta/professionTalentData'
import { GOD_COLORS } from '@/types'

interface Props {
  tree: ProfessionTalentTree
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'allocate', nodeId: string): void
  (e: 'deallocate', nodeId: string): void
  (e: 'reset'): void
  (e: 'close'): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const viewportRef = ref<HTMLElement | null>(null)
const panX = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const lastPanX = ref(0)
const hoveredNode = ref<ProfessionTalentNode | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

const sortedCoreTalents = computed(() => {
  const list = props.tree.coreTalents || []
  return [...list].sort((a, b) => {
    const ac = a.position?.col ?? 0
    const bc = b.position?.col ?? 0
    if (ac !== bc) return ac - bc
    return a.id.localeCompare(b.id)
  })
})

// 统一根据行列或已有坐标计算像素位置，方便支持无 x/y 的爬虫数据
function getNodeCoord(node: ProfessionTalentNode) {
  const { position } = node

  // 如果已经在数据里写死了 x/y，就直接用，兼容当前数据
  if (
    typeof position.x === 'number' &&
    typeof position.y === 'number' &&
    (position.x !== 0 || position.y !== 0)
  ) {
    return { x: position.x, y: position.y }
  }

  // 否则根据行列和网格配置计算
  const x = GRID_CONFIG.offsetX + position.col * GRID_CONFIG.colSpacing
  const y = GRID_CONFIG.offsetY + position.row * GRID_CONFIG.rowSpacing + 82 // 82 为第一行基准高度
  return { x, y }
}

function stripHtml(text: string): string {
  return text.replace(/<[^>]*>/g, '')
}

function getDisplayName(node: ProfessionTalentNode | null) {
  if (!node) return ''
  const rawName = (node.name || '').trim()
  const genericNames = ['小型天赋', '中型天赋', '传奇中型天赋']

  if (!genericNames.includes(rawName)) {
    return rawName
  }

  if (node.effects && node.effects.length > 0) {
    const first = stripHtml(node.effects[0]).trim()
    // 去掉前缀里的「小型天赋/中型天赋/传奇中型天赋」等字样
    const cleaned = first
      .replace(/^小型天赋[:：]?\s*/,'')
      .replace(/^中型天赋[:：]?\s*/,'')
      .replace(/^传奇中型天赋[:：]?\s*/,'')
      .trim()
    return cleaned || rawName
  }

  return rawName
}

function getDisplayMaxPoints(node: ProfessionTalentNode | null): number {
  if (!node) return 0
  return node.type === 'legendary' ? 1 : node.maxPoints
}

const svgWidth = computed(() => {
  const allNodes = [...props.tree.nodes, ...(props.tree.coreTalents || [])]
  const maxX = Math.max(...allNodes.map(n => getNodeCoord(n).x), 0)
  return maxX + 100
})

const svgHeight = computed(() => {
  const allNodes = [...props.tree.nodes, ...(props.tree.coreTalents || [])]
  const maxY = Math.max(...allNodes.map(n => getNodeCoord(n).y), 0)
  return maxY + 100
})

const coreSectionHeight = computed(() => {
  const coreNodes = props.tree.coreTalents || []
  if (!coreNodes.length) return 0
  const maxY = Math.max(...coreNodes.map(n => getNodeCoord(n).y), 0)
  // 预留节点自身高度和下边距
  return maxY + 150
})

const contentStyle = computed(() => {
  const viewportHeight = viewportRef.value?.clientHeight || 500
  const contentHeight = svgHeight.value
  const coreTalentHeight = 180
  const topOffset = coreTalentHeight
  
  return {
    width: `${svgWidth.value}px`,
    height: `${svgHeight.value}px`,
    transform: `translateX(${panX.value}px)`,
    top: `${topOffset}px`
  }
})

interface ConnectionPath {
  id: string
  path: string
  active: boolean
}

const connections = computed<ConnectionPath[]>(() => {
  const conns: ConnectionPath[] = []
  const nodeMap = new Map(props.tree.nodes.map(n => [n.id, n]))
  const connectionKeys = new Set<string>()

  for (const node of props.tree.nodes) {
    for (const parentId of node.connections) {
      const parentNode = nodeMap.get(parentId)
      if (parentNode) {
        const key = [parentId, node.id].sort().join('-')
        if (connectionKeys.has(key)) continue
        connectionKeys.add(key)

        // 使用节点视觉中心作为连线端点，避免小型/中型天赋之间连线错位
        const xOffset = GRID_CONFIG.nodeWidth / 2
        const yOffset = GRID_CONFIG.nodeHeight / 2

        const parentCoord = getNodeCoord(parentNode)
        const nodeCoord = getNodeCoord(node)

        const x1 = parentCoord.x + xOffset
        const y1 = parentCoord.y + yOffset
        const x2 = nodeCoord.x + xOffset
        const y2 = nodeCoord.y + yOffset

        const path = `M ${x1} ${y1} L ${x2} ${y2}`
        
        conns.push({
          id: key,
          path,
          active: parentNode.currentPoints > 0 && node.currentPoints > 0
        })
      }
    }
  }

  return conns
})

const tooltipStyle = computed(() => {
  const rect = containerRef.value?.getBoundingClientRect()
  if (!rect) return { left: '0px', top: '0px' }
  
  let left = tooltipPos.value.x + 15
  let top = tooltipPos.value.y + 15
  
  // 确保提示框在容器内
  const tooltipWidth = 320
  const tooltipHeight = 200
  
  if (left + tooltipWidth > rect.right) {
    left = tooltipPos.value.x - tooltipWidth - 15
  }
  
  if (top + tooltipHeight > rect.bottom) {
    top = tooltipPos.value.y - tooltipHeight - 15
  }
  
  return {
    left: `${left}px`,
    top: `${top}px`
  }
})

function getNodeStyle(node: ProfessionTalentNode) {
  const { x, y } = getNodeCoord(node)
  // 节点坐标基于图标中心计算，这里需要把外层盒子水平居中到该坐标
  const wrapperWidth = 120
  const iconWidth = GRID_CONFIG.nodeWidth
  const offsetX = (wrapperWidth - iconWidth) / 2
  return {
    left: `${x - offsetX}px`,
    top: `${y}px`
  }
}

function getLevelIndicatorStyle(level: number, index: number) {
  // 层级指示器应按「所有行的同一列」对齐，而不是只对齐第一行；
  // 0、3、6、9、12、15、18 分别对应第 0~6 列（纵向列）。
  const nodes = props.tree.nodes
  if (!nodes.length) {
    return { left: '0px' }
  }

  const xOffset = GRID_CONFIG.nodeWidth / 2

  const colNodes = nodes
    .filter(n => (n.position.col ?? 0) === index)
    .sort((a, b) => getNodeCoord(a).x - getNodeCoord(b).x)

  // 同一列的 x 理论上相同；若某列没有节点，则用网格配置兜底
  const x =
    colNodes.length > 0
      ? getNodeCoord(colNodes[0]).x
      : GRID_CONFIG.offsetX + index * GRID_CONFIG.colSpacing

  return {
    // 与节点外层盒子中心对齐（节点中心 x + 半个节点宽）
    left: `${x + xOffset}px`
  }
}

function getNodeColor(node: ProfessionTalentNode): string {
  if (node.currentPoints > 0) {
    return GOD_COLORS[props.tree.godType]
  }
  if (hoveredNode.value?.id === node.id) {
    return '#6a6a8a'
  }
  return '#3a3a5a'
}

function getNodeBackgroundColor(node: ProfessionTalentNode): string {
  if (node.currentPoints > 0) {
    return `${GOD_COLORS[props.tree.godType]}20`
  }
  if (hoveredNode.value?.id === node.id) {
    return '#6a6a8a20'
  }
  return 'transparent'
}

function getNodeTypeName(type: string, id?: string): string {
  if (id && id.startsWith('core_')) return '核心'
  switch (type) {
    case 'legendary': return '传奇'
    case 'notable': return '中型'
    default: return '小型'
  }
}

function getNodeIconPlaceholder(node: ProfessionTalentNode): string {
  switch (node.type) {
    case 'legendary': return '⚡'
    case 'notable': return '⭐'
    default: return '+'
  }
}

function getTalentIcon(node: ProfessionTalentNode): string {
  if (node.icon) {
    return node.icon
  }
  
  switch (node.type) {
    case 'legendary': return '/src/assets/talent/icons/legendary.svg'
    case 'notable': return '/src/assets/talent/icons/notable.svg'
    default: return '/src/assets/talent/icons/small.svg'
  }
}

function getNodeRequiredThreshold(node: ProfessionTalentNode): number {
  // 按「纵向列」来划分层级：
  // - 第 0 列 → LEVELS[0] = 0
  // - 第 1 列 → LEVELS[1] = 3
  // - 第 2 列 → LEVELS[2] = 6
  // 依此类推，同一列（纵向）共用同一个解锁门槛
  const colIndex = node.position.col ?? 0
  const levelIndex = Math.min(Math.max(colIndex, 0), LEVELS.length - 1)
  return LEVELS[levelIndex]
}

function isLocked(node: ProfessionTalentNode): boolean {
  // 1) 纵向层级逻辑：
  //    - 初始：第 0 列（9% 攻击伤害 / 3% 最大生命 / 7% 护甲）可以点
  //    - 当总点数 >= 3：解锁第 1 列整列
  //    - 当总点数 >= 6：解锁第 2 列整列，以此类推
  const threshold = getNodeRequiredThreshold(node)
  if (props.tree.allocatedPoints < threshold) {
    return true
  }

  // 2) 前置节点必须点满后，后续节点才允许加点：
  //    - 当前节点的 connections 里列出的，且在左侧列的节点视为前置节点
  const parents = props.tree.nodes.filter(
    n =>
      node.connections.includes(n.id) &&
      (n.position.col ?? 0) < (node.position.col ?? 0)
  )

  if (parents.length === 0) {
    return false
  }

  // 只有当所有前置节点都点满时，当前节点才解锁
  const allParentsMaxed = parents.every(
    p => p.currentPoints >= p.maxPoints
  )

  return !allParentsMaxed
}

function onNodeClick(node: ProfessionTalentNode) {
  // 核心天赋：受自身 requiredPoints 限制（如 24pts），与天赋树总加点数联动
  if (node.id.startsWith('core_')) {
    if (props.tree.allocatedPoints < node.requiredPoints) return
    const maxPoints = getDisplayMaxPoints(node)
    if (node.currentPoints >= maxPoints) return
    emit('allocate', node.id)
    return
  }

  if (isLocked(node)) return
  
  // 左键只负责加点，直到达到 maxPoints 为止
  const maxPoints = getDisplayMaxPoints(node)
  if (node.currentPoints >= maxPoints) return
  emit('allocate', node.id)
}

function onNodeRightClick(node: ProfessionTalentNode, event: MouseEvent) {
  event.preventDefault()
  // 减点校验与提示统一由 store.deallocateNode 处理（含后续层依赖检测）
  if (node.currentPoints > 0) {
    emit('deallocate', node.id)
  }
}

function onNodeHover(node: ProfessionTalentNode, event: MouseEvent) {
  hoveredNode.value = node
  tooltipPos.value = { x: event.clientX, y: event.clientY }
}

function onNodeLeave() {
  hoveredNode.value = null
}

function startDrag(e: MouseEvent) {
  if ((e.target as HTMLElement).closest('.talent-node-wrapper')) return
  isDragging.value = true
  dragStart.value = { x: e.clientX, y: e.clientY }
  lastPanX.value = panX.value
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  const dx = e.clientX - dragStart.value.x
  panX.value = lastPanX.value + dx
}

function endDrag() {
  isDragging.value = false
}

function resetTree() {
  emit('reset')
}

// 监听窗口大小变化，自动调整画布位置
function adjustCanvasPosition() {
  if (viewportRef.value) {
    const containerWidth = viewportRef.value.clientWidth
    const contentWidth = svgWidth.value
    // 左对齐：只在内容比容器窄时保持在最左侧
    panX.value = 0
  }
}

onMounted(() => {
  adjustCanvasPosition()
  window.addEventListener('resize', adjustCanvasPosition)
})

// 清理事件监听器
function onUnmounted() {
  window.removeEventListener('resize', adjustCanvasPosition)
}
</script>

<style scoped>
.profession-tree-container {
  position: relative;
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 50%, #0f0f1a 100%);
  user-select: none;
  overflow: hidden;
}

.tree-header {
  flex-shrink: 0;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  background: rgba(0, 0, 0, 0.6);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  z-index: 10;
  backdrop-filter: blur(10px);
}

.profession-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profession-name {
  font-size: 20px;
  font-weight: bold;
  color: #fff;
  margin: 0;
  text-shadow: 0 0 10px rgba(233, 69, 96, 0.5);
}

.profession-tags {
  display: flex;
  gap: 10px;
}

.tag {
  padding: 4px 12px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  font-size: 12px;
  color: #aaa;
  transition: all 0.3s ease;
}

.tag:hover {
  background: rgba(255, 255, 255, 0.15);
  color: #fff;
  transform: translateY(-1px);
}

.points-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.close-btn {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(0, 0, 0, 0.25);
  color: rgba(255, 255, 255, 0.85);
  font-size: 18px;
  line-height: 24px;
  cursor: pointer;
  transition: all 0.18s ease;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.points-text {
  font-size: 16px;
  color: #ffd700;
  font-weight: bold;
  text-shadow: 0 0 8px rgba(255, 215, 0, 0.5);
}

.reset-btn {
  padding: 8px 16px;
  background: rgba(255, 100, 100, 0.2);
  border: 1px solid rgba(255, 100, 100, 0.5);
  border-radius: 6px;
  color: #ff6464;
  cursor: pointer;
  font-size: 13px;
  transition: all 0.3s ease;
  font-weight: 500;
}

.reset-btn:hover {
  background: rgba(255, 100, 100, 0.3);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 100, 100, 0.3);
}

.tree-viewport {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.tree-content {
  position: absolute;
  top: 0;
  left: 0;
  cursor: grab;
  transition: transform 0.2s ease;
}

.tree-content:active {
  cursor: grabbing;
}

/* 背景装饰 */
.background-decor {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.decor-circle {
  position: absolute;
  width: 200px;
  height: 200px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(233, 69, 96, 0.1) 0%, transparent 70%);
  animation: pulse 8s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% {
    transform: scale(1);
    opacity: 0.3;
  }
  50% {
    transform: scale(1.1);
    opacity: 0.5;
  }
}

/* 层级指示器 */
.level-indicators {
  position: absolute;
  top: 40px;
  left: 0;
  width: 100%;
  z-index: 5;
}

.level-line {
  position: absolute;
  /* 与 30px 高的圆形指示器垂直居中对齐 */
  top: 15px;
  left: 0;
  right: 0;
  height: 2px;
  background: #ffd700; /* 与文字颜色一致 */
  opacity: 0.4;
  transform: none;
  pointer-events: none;
}

.level-indicator {
  position: absolute;
  width: 30px;
  height: 30px;
  background: rgba(0, 0, 0, 0.8);
  border: 2px solid #333;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  transform: translateX(-50%);
  transition: all 0.3s ease;
  z-index: 1; /* 指示器在横线之上 */
}

.level-indicator:hover {
  background: rgba(0, 0, 0, 0.9);
  border-color: #555;
  transform: translateX(-50%) scale(1.1);
}

.level-number {
  font-size: 12px;
  color: #ffd700;
  font-weight: bold;
  line-height: 1;
}

.level-label {
  font-size: 8px;
  color: #aaa;
  margin-top: 2px;
}

/* 网格线 */
.grid-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.grid-line {
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 1;
  stroke-dasharray: 5, 5;
  transition: stroke 0.3s ease;
}

/* 连接线 */
.connections-svg {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 2;
}

.connection-path {
  fill: none;
  stroke: #2a2a4a;
  stroke-width: 3;
  stroke-linecap: round;
  transition: all 0.3s ease;
}

.connection-path.active {
  stroke: #e94560;
  stroke-width: 4;
  filter: drop-shadow(0 0 8px currentColor);
  animation: pulse-connection 2s ease-in-out infinite;
}

@keyframes pulse-connection {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
}

/* 天赋节点 */
.talent-node-wrapper {
  position: absolute;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 120px;
  cursor: pointer;
  transition: all 0.3s ease;
  z-index: 3;
  transform-origin: center;
}

.talent-node-wrapper.locked {
  opacity: 0.4;
  cursor: not-allowed;
}

.talent-node-wrapper:not(.locked):hover {
  transform: translateY(-2px);
  filter: brightness(1.3);
}

.talent-node-wrapper.hovered {
  filter: brightness(1.4);
}

.node-icon {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.node-background {
  position: absolute;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  transition: all 0.3s ease;
  z-index: -1;
}

.talent-node-wrapper.allocated .node-background {
  box-shadow: 0 0 20px currentColor;
  animation: glow 2s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% {
    box-shadow: 0 0 20px currentColor;
  }
  50% {
    box-shadow: 0 0 30px currentColor, 0 0 40px currentColor;
  }
}

.node-ring {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  border: 3px solid #3a3a5a;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.5);
  transition: all 0.3s ease;
  position: relative;
}

.talent-node-wrapper.allocated .node-ring {
  background: rgba(233, 69, 96, 0.2);
  box-shadow: 0 0 15px rgba(233, 69, 96, 0.5);
  border-width: 4px;
}

.talent-node-wrapper.legendary .node-ring {
  width: 60px;
  height: 60px;
  border-width: 4px;
}

.talent-node-wrapper.legendary.allocated .node-ring {
  background: linear-gradient(135deg, rgba(233, 69, 96, 0.3), rgba(255, 215, 0, 0.3));
  box-shadow: 0 0 25px rgba(255, 215, 0, 0.6);
  animation: legendary-glow 2s ease-in-out infinite;
}

@keyframes legendary-glow {
  0%, 100% {
    box-shadow: 0 0 25px rgba(255, 215, 0, 0.6);
  }
  50% {
    box-shadow: 0 0 35px rgba(255, 215, 0, 0.8), 0 0 45px rgba(255, 215, 0, 0.4);
  }
}

.talent-node-wrapper.notable .node-ring {
  width: 55px;
  height: 55px;
  border-width: 3.5px;
}

.talent-node-wrapper.notable.allocated .node-ring {
  background: rgba(74, 144, 217, 0.2);
  box-shadow: 0 0 20px rgba(74, 144, 217, 0.6);
}

.node-points {
  font-size: 13px;
  color: #fff;
  font-weight: bold;
  text-shadow: 0 0 4px rgba(0, 0, 0, 0.8);
}

.node-check {
  font-size: 22px;
  color: #ffd700;
  text-shadow: 0 0 6px rgba(255, 215, 0, 0.6);
}

.node-icon-placeholder {
  font-size: 20px;
  color: #666;
  transition: color 0.3s ease;
}

.node-icon-container {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
  height: 100%;
}

.node-icon-image {
  width: 60%;
  height: 60%;
  object-fit: contain;
  transition: all 0.3s ease;
}

.talent-node-wrapper:hover .node-icon-image {
  transform: scale(1.1);
  filter: brightness(1.3);
}

.node-name {
  margin-top: 10px;
  font-size: 11px;
  color: #888;
  text-align: center;
  max-width: 200px;
  word-break: break-all;
  line-height: 1.3;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2; /* 最多显示两行 */
  -webkit-box-orient: vertical;
  transition: all 0.3s ease;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
}

.talent-node-wrapper.allocated .node-name {
  color: #fff;
  font-weight: 500;
}

.talent-node-wrapper:hover .node-name {
  color: #ddd;
  transform: translateY(-1px);
}

/* 提示框 */
.node-tooltip {
  position: fixed;
  background: rgba(20, 20, 35, 0.95);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 20px;
  max-width: 320px;
  z-index: 100;
  pointer-events: none;
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.05);
  animation: tooltip-appear 0.3s ease-out;
}

@keyframes tooltip-appear {
  from {
    opacity: 0;
    transform: scale(0.9) translate(-10px, -10px);
  }
  to {
    opacity: 1;
    transform: scale(1) translate(0, 0);
  }
}

.tooltip-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 14px;
}

.tooltip-type {
  padding: 3px 10px;
  border-radius: 6px;
  font-size: 10px;
  text-transform: uppercase;
  font-weight: bold;
  letter-spacing: 0.5px;
}

.tooltip-type.legendary {
  background: linear-gradient(135deg, #ffd700, #ff8c00);
  color: #000;
  box-shadow: 0 2px 8px rgba(255, 215, 0, 0.3);
}

.tooltip-type.notable {
  background: linear-gradient(135deg, #4a90d9, #357abd);
  color: #fff;
  box-shadow: 0 2px 8px rgba(74, 144, 217, 0.3);
}

.tooltip-type.small {
  background: linear-gradient(135deg, #555, #333);
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.tooltip-type.core {
  background: linear-gradient(135deg, #ff4b4b, #b31217);
  color: #fff;
  box-shadow: 0 2px 10px rgba(255, 75, 75, 0.5);
}

.tooltip-name {
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.2);
}

.tooltip-effects {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 12px;
}

.effect-line {
  font-size: 14px;
  color: #ccc;
  margin: 0;
  line-height: 1.4;
  position: relative;
  padding-left: 12px;
}

.effect-line::before {
  content: '•';
  position: absolute;
  left: 0;
  color: #e94560;
  font-weight: bold;
}

.tooltip-requirement {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 12px;
  color: #ff6464;
  font-weight: 500;
}

.tooltip-points {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: #aaa;
}

.points-label {
  font-weight: 500;
}

.points-value {
  color: #ffd700;
  font-weight: bold;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .tree-header {
    padding: 12px 16px;
  }
  
  .profession-name {
    font-size: 18px;
  }
  
  .points-text {
    font-size: 14px;
  }
  
  .reset-btn {
    padding: 6px 12px;
    font-size: 12px;
  }
  
  .node-name {
    font-size: 10px;
  }
  
  .node-tooltip {
    max-width: 280px;
    padding: 16px;
  }
  
  .tooltip-name {
    font-size: 14px;
  }
  
  .effect-line {
    font-size: 13px;
  }
}

/* 核心天赋区域 */
.core-talents-section {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: auto;
  min-height: 120px;
  background: rgba(0, 0, 0, 0.3);
  border-bottom: 2px solid rgba(255, 255, 255, 0.1);
  z-index: 20;
  overflow: hidden;
}

.core-talents-title {
  position: absolute;
  top: 10px;
  left: 20px;
  font-size: 14px;
  font-weight: bold;
  color: #ffd700;
  text-transform: uppercase;
  letter-spacing: 1px;
  z-index: 21;
}

.core-talents-container {
  position: relative;
  width: 100%;
  height: auto;
  min-height: 80px;
  /* 让内容不出现滚动条，由父容器高度自适应 */
  overflow: visible;
  padding: 20px;
  display: flex;
  gap: 16px;
  align-items: center;
}

.core-talents-divider {
  width: 1px;
  height: 72px;
  background: linear-gradient(
    to bottom,
    transparent,
    rgba(255, 255, 255, 0.18),
    transparent
  );
  flex: 0 0 1px;
  margin: 0 6px;
}

.core-talent-node {
  width: 140px;
  height: auto;
  min-height: 80px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px;
  background: rgba(20, 20, 35, 0.8);
  border: 2px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
}

.core-talent-node:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(255, 215, 0, 0.3);
  border-color: rgba(255, 215, 0, 0.5);
}

.core-talent-node.allocated {
  background: rgba(255, 215, 0, 0.15);
  border-color: #ffd700;
  box-shadow: 0 0 20px rgba(255, 215, 0, 0.4);
}

.core-talent-node.locked {
  opacity: 0.5;
  cursor: not-allowed;
}

.core-talent-icon {
  position: relative;
  width: 60px;
  height: 60px;
  margin-bottom: 6px;
}

.core-talent-background {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: transparent;
  transition: background 0.3s ease;
}

.core-talent-ring {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  background: rgba(0, 0, 0, 0.5);
}

.core-talent-node:hover .core-talent-ring {
  border-color: #ffd700;
  box-shadow: 0 0 15px rgba(255, 215, 0, 0.5);
}

.core-talent-node.allocated .core-talent-ring {
  border-color: #ffd700;
  background: rgba(255, 215, 0, 0.2);
}

.core-talent-check {
  font-size: 40px;
  color: #ffd700;
  font-weight: bold;
}

.core-talent-icon-container {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.core-talent-icon-image {
  width: 48px;
  height: 48px;
  object-fit: contain;
}

.core-talent-info {
  text-align: center;
}

.core-talent-name {
  font-size: 12px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 4px;
  text-shadow: 0 1px 3px rgba(0, 0, 0, 0.5);
}

.core-talent-points {
  font-size: 10px;
  color: #aaa;
}

.core-talent-node.allocated .core-talent-name {
  color: #ffd700;
}

.core-talent-node.allocated .core-talent-points {
  color: #ffd700;
}
</style>