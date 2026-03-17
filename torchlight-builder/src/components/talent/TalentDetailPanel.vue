<template>
  <div class="talent-detail-panel" v-if="node">
    <div class="panel-header" :style="{ borderColor: nodeColor }">
      <div class="node-icon" :style="{ background: nodeColor }">
        <span class="node-type-icon">{{ typeIcon }}</span>
      </div>
      <div class="node-info">
        <h3 class="node-name">{{ node.name }}</h3>
        <span class="node-type" :style="{ color: nodeColor }">{{ typeLabel }}</span>
      </div>
    </div>

    <div class="panel-body">
      <p class="node-description">{{ node.description }}</p>

      <div class="effects-section" v-if="node.effects.length > 0">
        <h4>效果</h4>
        <ul class="effects-list">
          <li v-for="(effect, index) in node.effects" :key="index" class="effect-item">
            <span class="effect-icon" :class="effect.type">◆</span>
            <span class="effect-text">{{ effect.description }}</span>
          </li>
        </ul>
      </div>

      <div class="requirements-section" v-if="node.requirements">
        <h4>需求</h4>
        <div class="requirements-list">
          <span v-if="node.requirements.level" class="requirement">
            等级: {{ node.requirements.level }}
          </span>
          <span v-if="node.requirements.nodes?.length" class="requirement">
            需要连接节点
          </span>
        </div>
      </div>

      <div class="actions-section">
        <button
          class="action-btn allocate"
          v-if="!node.allocated"
          @click="$emit('allocate')"
          :disabled="!canAllocate"
        >
          分配天赋点
        </button>
        <button
          class="action-btn deallocate"
          v-else
          @click="$emit('deallocate')"
        >
          取消分配
        </button>
      </div>
    </div>
  </div>

  <div class="talent-detail-panel empty" v-else>
    <div class="empty-hint">
      <span class="hint-icon">◎</span>
      <p>点击天赋节点查看详情</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { TalentNode } from '@/types'
import { GOD_COLORS } from '@/types'

interface Props {
  node: TalentNode | null
  canAllocate?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  canAllocate: true
})

defineEmits<{
  (e: 'allocate'): void
  (e: 'deallocate'): void
}>()

const nodeColor = computed(() => {
  if (!props.node) return '#666'
  return GOD_COLORS[props.node.godType || 'strength']
})

const typeIcon = computed(() => {
  if (!props.node) return ''
  switch (props.node.type) {
    case 'keystone':
      return '★'
    case 'notable':
      return '◆'
    default:
      return '●'
  }
})

const typeLabel = computed(() => {
  if (!props.node) return ''
  switch (props.node.type) {
    case 'keystone':
      return '核心天赋'
    case 'notable':
      return '重要天赋'
    default:
      return '普通天赋'
  }
})
</script>

<style scoped>
.talent-detail-panel {
  background: linear-gradient(180deg, #1a1a2e 0%, #0f0f1a 100%);
  border: 1px solid var(--border-color);
  border-radius: 8px;
  padding: 1rem;
  min-height: 300px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid;
  margin-bottom: 1rem;
}

.node-icon {
  width: 48px;
  height: 48px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: #fff;
}

.node-info {
  flex: 1;
}

.node-name {
  margin: 0;
  font-size: 1.25rem;
  color: #fff;
}

.node-type {
  font-size: 0.875rem;
  opacity: 0.8;
}

.panel-body {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.node-description {
  color: #a0a0a0;
  line-height: 1.6;
  margin: 0;
}

.effects-section h4,
.requirements-section h4 {
  color: #fff;
  margin: 0 0 0.5rem 0;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.effects-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.effect-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  margin-bottom: 0.25rem;
}

.effect-icon {
  color: #4ade80;
}

.effect-icon.modifier {
  color: #60a5fa;
}

.effect-icon.special {
  color: #fbbf24;
}

.effect-text {
  color: #e0e0e0;
  font-size: 0.875rem;
}

.requirements-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.requirement {
  padding: 0.25rem 0.75rem;
  background: rgba(233, 69, 96, 0.2);
  border-radius: 4px;
  font-size: 0.75rem;
  color: #e94560;
}

.actions-section {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--border-color);
}

.action-btn {
  width: 100%;
  padding: 0.75rem;
  border: none;
  border-radius: 4px;
  font-size: 1rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.action-btn.allocate {
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  color: #fff;
}

.action-btn.allocate:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(233, 69, 96, 0.4);
}

.action-btn.allocate:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.action-btn.deallocate {
  background: transparent;
  border: 1px solid #e94560;
  color: #e94560;
}

.action-btn.deallocate:hover {
  background: rgba(233, 69, 96, 0.1);
}

.empty {
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-hint {
  text-align: center;
  color: #666;
}

.hint-icon {
  font-size: 3rem;
  display: block;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.empty-hint p {
  margin: 0;
}
</style>
