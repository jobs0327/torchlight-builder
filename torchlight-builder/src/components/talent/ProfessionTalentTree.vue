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
        <button class="reset-btn" @click="resetTree">重置</button>
      </div>
    </div>

    <div class="tree-viewport" ref="viewportRef">
      <!-- 核心天赋区域 -->
      <div class="core-talents-section">
        <div class="core-talents-title">核心天赋</div>
        <div class="core-talents-container">
          <div 
            v-for="node in tree.coreTalents" 
            :key="node.id"
            :class="['core-talent-node', { allocated: node.currentPoints > 0, locked: isLocked(node), hovered: hoveredNode?.id === node.id }]"
            :style="getCoreTalentStyle(node)"
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
          <div 
            v-for="(level, index) in LEVELS" 
            :key="index"
            class="level-indicator"
            :style="getLevelIndicatorStyle(index)"
          >
            <span class="level-number">{{ level }}</span>
            <div class="level-label">点</div>
          </div>
        </div>

        <!-- 网格线 -->
        <svg class="grid-svg" :viewBox="`0 0 ${svgWidth} ${svgHeight}`">
          <g class="grid-lines">
            <!-- 水平线 - 基于实际节点位置 -->
            <line 
              v-for="(y, index) in [82, 178, 274, 370, 466]" 
              :key="`h-${index}`"
              :x1="0" 
              :y1="y"
              :x2="svgWidth" 
              :y2="y"
              class="grid-line horizontal"
            />
            <!-- 垂直线 - 基于实际节点位置 -->
            <line 
              v-for="(x, index) in [136, 272, 408, 544, 672, 808]" 
              :key="`v-${index}`"
              :x1="x"
              :y1="0" 
              :x2="x"
              :y2="svgHeight"
              class="grid-line vertical"
            />
          </g>
        </svg>

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
              <span v-if="node.maxPoints > 1 && node.currentPoints > 0" class="node-points">
                {{ node.currentPoints }}/{{ node.maxPoints }}
              </span>
              <span v-else-if="node.currentPoints > 0" class="node-check">✓</span>
              <div v-else class="node-icon-container">
                <img 
                  :src="getTalentIcon(node)" 
                  :alt="node.name"
                  class="node-icon-image"
                />
              </div>
            </div>
          </div>
          <div class="node-name">{{ node.name }}</div>
        </div>
      </div>
    </div>

    <div v-if="hoveredNode" class="node-tooltip" :style="tooltipStyle">
      <div class="tooltip-header">
        <span :class="['tooltip-type', hoveredNode.type]">{{ getNodeTypeName(hoveredNode.type) }}</span>
        <span class="tooltip-name">{{ hoveredNode.name }}</span>
      </div>
      <div class="tooltip-effects">
        <p v-for="(effect, index) in hoveredNode.effects" :key="index" class="effect-line">
          {{ effect }}
        </p>
      </div>
      <div v-if="hoveredNode.requiredPoints > 0" class="tooltip-requirement">
        需要 {{ hoveredNode.requiredPoints }} 点已分配
      </div>
      <div class="tooltip-points">
        <span class="points-label">可分配点数:</span>
        <span class="points-value">{{ hoveredNode.maxPoints }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue'
import type { ProfessionTalentTree, ProfessionTalentNode } from '@/data/professionTalentData'
import { GRID_CONFIG, LEVELS } from '@/data/professionTalentData'
import { GOD_COLORS } from '@/types'

interface Props {
  tree: ProfessionTalentTree
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'allocate', nodeId: string): void
  (e: 'deallocate', nodeId: string): void
  (e: 'reset'): void
}>()

const containerRef = ref<HTMLElement | null>(null)
const viewportRef = ref<HTMLElement | null>(null)
const panX = ref(0)
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const lastPanX = ref(0)
const hoveredNode = ref<ProfessionTalentNode | null>(null)
const tooltipPos = ref({ x: 0, y: 0 })

const svgWidth = computed(() => {
  const maxX = Math.max(...props.tree.nodes.map(n => n.position.x), 0)
  return maxX + 100
})

const svgHeight = computed(() => {
  const maxY = Math.max(...props.tree.nodes.map(n => n.position.y), 0)
  return maxY + 100
})

const contentStyle = computed(() => {
  const viewportHeight = viewportRef.value?.clientHeight || 500
  const contentHeight = svgHeight.value
  const coreTalentHeight = 180
  const topOffset = Math.max(coreTalentHeight, (viewportHeight - contentHeight) / 2)
  
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

        const x1 = parentNode.position.x
        const y1 = parentNode.position.y
        const x2 = node.position.x
        const y2 = node.position.y

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
  return {
    left: `${node.position.x}px`,
    top: `${node.position.y}px`
  }
}

function getCoreTalentStyle(node: ProfessionTalentNode) {
  return {
    left: `${node.position.x}px`,
    top: `${node.position.y}px`
  }
}

function getLevelIndicatorStyle(index: number) {
  const level = LEVELS[index]
  let x = 0
  
  switch(level) {
    case 0: x = 128; break
    case 3: x = 192; break
    case 6: x = 384; break
    case 9: x = 448; break
    case 12: x = 640; break
    case 15: x = 704; break
    case 18: x = 768; break
    default: x = 128
  }
  
  return {
    left: `${x}px`
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

function getNodeTypeName(type: string): string {
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

function isLocked(node: ProfessionTalentNode): boolean {
  if (props.tree.allocatedPoints < node.requiredPoints) {
    return true
  }
  
  for (const parentId of node.connections) {
    const parentNode = props.tree.nodes.find(n => n.id === parentId)
    if (parentNode && parentNode.currentPoints === 0) {
      return true
    }
  }
  
  return false
}

function onNodeClick(node: ProfessionTalentNode) {
  if (isLocked(node)) return
  
  if (node.currentPoints >= node.maxPoints) {
    const hasAllocatedChildren = props.tree.nodes.some(n => 
      n.connections.includes(node.id) && n.currentPoints > 0
    )
    if (hasAllocatedChildren) return
    emit('deallocate', node.id)
  } else {
    emit('allocate', node.id)
  }
}

function onNodeRightClick(node: ProfessionTalentNode, event: MouseEvent) {
  event.preventDefault()
  if (node.currentPoints > 0) {
    const hasAllocatedChildren = props.tree.nodes.some(n => 
      n.connections.includes(node.id) && n.currentPoints > 0
    )
    if (hasAllocatedChildren && node.currentPoints === 1) return
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
    if (contentWidth > containerWidth) {
      panX.value = 0
    } else {
      panX.value = (containerWidth - contentWidth) / 2
    }
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
  width: 80px;
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
  max-width: 70px;
  word-break: break-all;
  line-height: 1.3;
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
  overflow: auto;
  padding: 40px 20px 20px;
}

.core-talent-node {
  position: absolute;
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