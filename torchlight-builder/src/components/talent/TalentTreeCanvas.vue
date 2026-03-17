<template>
  <svg
    ref="svgRef"
    class="talent-tree-canvas"
    :viewBox="`0 0 ${width} ${height}`"
    @mousedown="startDrag"
    @mousemove="onDrag"
    @mouseup="endDrag"
    @mouseleave="endDrag"
    @wheel="onZoom"
  >
    <g :transform="`translate(${pan.x}, ${pan.y}) scale(${scale})`">
      <g class="connections">
        <line
          v-for="conn in connections"
          :key="conn.id"
          :x1="conn.x1"
          :y1="conn.y1"
          :x2="conn.x2"
          :y2="conn.y2"
          :class="['connection-line', { active: conn.active }]"
          :style="{ stroke: conn.color }"
        />
      </g>

      <g class="nodes">
        <g
          v-for="node in nodes"
          :key="node.id"
          :transform="`translate(${node.position.x}, ${node.position.y})`"
          class="talent-node-group"
          @click.stop="onNodeClick(node)"
          @mouseenter="onNodeHover(node)"
          @mouseleave="onNodeLeave"
        >
          <circle
            :r="getNodeRadius(node.type)"
            :class="['talent-node', node.type, { allocated: node.allocated, hover: hoveredNode?.id === node.id }]"
            :style="{ fill: getNodeColor(node) }"
          />
          <circle
            v-if="node.allocated"
            :r="getNodeRadius(node.type) - 4"
            class="node-inner allocated-inner"
          />
          <text
            :y="getNodeRadius(node.type) + 15"
            class="node-label"
            text-anchor="middle"
          >
            {{ node.name }}
          </text>
        </g>
      </g>
    </g>
  </svg>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import type { TalentNode, TalentTree, GodType } from '@/types'
import { GOD_COLORS } from '@/types'

interface Props {
  tree: TalentTree
  width?: number
  height?: number
}

const props = withDefaults(defineProps<Props>(), {
  width: 600,
  height: 600
})

const emit = defineEmits<{
  (e: 'nodeClick', node: TalentNode): void
  (e: 'nodeHover', node: TalentNode | null): void
}>()

const svgRef = ref<SVGSVGElement | null>(null)
const nodes = computed(() => props.tree.nodes)

const scale = ref(1)
const pan = ref({ x: 0, y: 0 })
const isDragging = ref(false)
const dragStart = ref({ x: 0, y: 0 })
const hoveredNode = ref<TalentNode | null>(null)

interface ConnectionData {
  id: string
  x1: number
  y1: number
  x2: number
  y2: number
  active: boolean
  color: string
}

const connections = computed<ConnectionData[]>(() => {
  const conns: ConnectionData[] = []
  const nodeMap = new Map(nodes.value.map(n => [n.id, n]))

  for (const node of nodes.value) {
    for (const connId of node.connections) {
      const targetNode = nodeMap.get(connId)
      if (targetNode) {
        const isActive = node.allocated && targetNode.allocated
        conns.push({
          id: `${node.id}-${connId}`,
          x1: node.position.x,
          y1: node.position.y,
          x2: targetNode.position.x,
          y2: targetNode.position.y,
          active: isActive,
          color: isActive ? GOD_COLORS[node.godType || 'strength'] : '#2a2a4a'
        })
      }
    }
  }

  return conns
})

function getNodeRadius(type: string): number {
  switch (type) {
    case 'keystone':
      return 30
    case 'notable':
      return 22
    default:
      return 16
  }
}

function getNodeColor(node: TalentNode): string {
  if (node.allocated) {
    return GOD_COLORS[node.godType || 'strength']
  }
  return '#2a2a4a'
}

function onNodeClick(node: TalentNode) {
  emit('nodeClick', node)
}

function onNodeHover(node: TalentNode) {
  hoveredNode.value = node
  emit('nodeHover', node)
}

function onNodeLeave() {
  hoveredNode.value = null
  emit('nodeHover', null)
}

function startDrag(e: MouseEvent) {
  isDragging.value = true
  dragStart.value = { x: e.clientX - pan.value.x, y: e.clientY - pan.value.y }
}

function onDrag(e: MouseEvent) {
  if (!isDragging.value) return
  pan.value = {
    x: e.clientX - dragStart.value.x,
    y: e.clientY - dragStart.value.y
  }
}

function endDrag() {
  isDragging.value = false
}

function onZoom(e: WheelEvent) {
  e.preventDefault()
  const delta = e.deltaY > 0 ? 0.9 : 1.1
  const newScale = Math.max(0.5, Math.min(2, scale.value * delta))
  scale.value = newScale
}

function resetView() {
  scale.value = 1
  pan.value = { x: 0, y: 0 }
}

defineExpose({ resetView })
</script>

<style scoped>
.talent-tree-canvas {
  width: 100%;
  height: 100%;
  cursor: grab;
  background: radial-gradient(circle at center, #1a1a2e 0%, #0f0f1a 100%);
}

.talent-tree-canvas:active {
  cursor: grabbing;
}

.connection-line {
  stroke-width: 3;
  stroke-linecap: round;
  transition: stroke 0.3s ease;
}

.connection-line.active {
  stroke-width: 4;
  filter: drop-shadow(0 0 4px currentColor);
}

.talent-node-group {
  cursor: pointer;
}

.talent-node {
  stroke-width: 3;
  stroke: #3a3a5a;
  transition: all 0.2s ease;
}

.talent-node-group:hover .talent-node {
  stroke-width: 5;
  filter: drop-shadow(0 0 15px currentColor);
}

.talent-node.allocated {
  stroke: currentColor;
  filter: drop-shadow(0 0 8px currentColor);
}

.talent-node.hover {
  stroke-width: 4;
  filter: drop-shadow(0 0 12px currentColor);
}

.talent-node.keystone {
  stroke-width: 4;
}

.node-inner.allocated-inner {
  fill: rgba(255, 255, 255, 0.3);
  stroke: none;
}

.node-label {
  fill: #a0a0a0;
  font-size: 10px;
  pointer-events: none;
  user-select: none;
}

.talent-node.allocated + .node-label,
.talent-node-group:hover .node-label {
  fill: #ffffff;
}
</style>
