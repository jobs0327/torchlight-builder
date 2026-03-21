<template>
  <div class="skill-card">
    <div class="skill-card-head">
      <div class="skill-card-title-wrap">
        <div class="skill-card-title">{{ title }}</div>
        <div class="skill-card-role" :class="`role-${role}`">{{ roleLabel }}</div>
      </div>
      <div class="skill-card-count">辅助连接 {{ supportCount }}/5</div>
    </div>

    <div class="link-diagram">
      <svg class="link-lines" viewBox="0 0 100 100" preserveAspectRatio="none" aria-hidden="true">
        <line
          v-for="(p, idx) in supportPoints"
          :key="`line-${idx}`"
          x1="50"
          y1="50"
          :x2="p.x"
          :y2="p.y"
          stroke="rgba(255,255,255,0.24)"
          stroke-width="1.2"
        />
      </svg>

      <button
        type="button"
        class="node node-main"
        :class="{ active: editingSlot === 'main', filled: !!mainSkillName }"
        @click="editingSlot = 'main'"
      >
        <span class="node-label">核心</span>
        <span class="node-name">{{ mainSkillName || '点击选择技能' }}</span>
      </button>

      <button
        v-for="(sid, idx) in modelValue.supportSkillIds"
        :key="`support-${idx}`"
        type="button"
        class="node node-support"
        :class="{ active: editingSlot === idx, filled: !!supportSkillNameByIndex(idx) }"
        :style="supportNodeStyleByIndex(idx)"
        @click="editingSlot = idx"
      >
        <span class="node-label">辅{{ idx + 1 }}</span>
        <span class="node-name">{{ supportSkillNameByIndex(idx) || '未连接' }}</span>
      </button>
    </div>

    <div class="picker-panel">
      <div class="picker-head">
        <span class="picker-title">{{ pickerTitle }}</span>
        <button
          v-if="editingSlot !== null"
          type="button"
          class="picker-clear"
          @click="clearCurrentSlot"
        >
          清空
        </button>
      </div>
      <div class="picker-options">
        <div class="picker-tags">
          <button
            v-for="tag in availableTags"
            :key="`tag-${tag}`"
            type="button"
            class="tag-chip"
            :class="{ active: selectedTag === tag }"
            @click="selectedTag = tag"
          >
            {{ tag }}
          </button>
        </div>
        <div class="picker-divider"></div>
        <div class="opt-list">
          <button
            v-for="opt in filteredOptions"
            :key="opt.id"
            type="button"
            class="opt-chip"
            @click="applyOption(opt.id)"
          >
            <img
              v-if="opt.iconUrl"
              :src="opt.iconUrl"
              :alt="opt.name"
              class="opt-icon"
              loading="lazy"
            />
            <span class="opt-name">{{ opt.name }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'

type SkillOption = {
  id: string
  name: string
  iconUrl?: string
  tags?: string[]
}

type SkillLinkItem = {
  mainSkillId: string
  supportSkillIds: string[]
}

type SkillRole = 'core' | 'active' | 'passive'

interface Props {
  title: string
  role: SkillRole
  modelValue: SkillLinkItem
  mainOptions: SkillOption[]
  supportOptions: SkillOption[]
  tagWhitelist?: string[]
  requireTagToShowOptions?: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: SkillLinkItem): void
}>()

const editingSlot = ref<'main' | number | null>('main')
const selectedTag = ref<string>('全部')

const roleLabel = computed(() => {
  if (props.role === 'core') return '核心技能'
  if (props.role === 'active') return '主动技能'
  return '被动技能'
})

const supportCount = computed(
  () => props.modelValue.supportSkillIds.filter(v => (v ?? '').trim().length > 0).length
)

const supportPoints = [
  { x: 50, y: 13 },
  { x: 16, y: 37 },
  { x: 29, y: 77 },
  { x: 71, y: 77 },
  { x: 84, y: 37 }
]

const mainSkillName = computed(() => {
  const hit = props.mainOptions.find(opt => opt.id === props.modelValue.mainSkillId)
  return hit?.name ?? ''
})

function supportSkillNameByIndex(index: number) {
  const id = props.modelValue.supportSkillIds[index]
  const hit = props.supportOptions.find(opt => opt.id === id)
  return hit?.name ?? ''
}

function supportNodeStyleByIndex(index: number) {
  const p = supportPoints[index]
  return {
    left: `${p.x}%`,
    top: `${p.y}%`
  }
}

const pickerTitle = computed(() => {
  if (editingSlot.value === 'main') return '选择主技能'
  if (typeof editingSlot.value === 'number') return `选择辅助 ${editingSlot.value + 1}`
  return '请选择一个节点'
})

const currentOptions = computed(() => {
  if (editingSlot.value === 'main') return props.mainOptions
  if (typeof editingSlot.value === 'number') return props.supportOptions
  return []
})

const availableTags = computed(() => {
  const hit = new Set<string>()
  const sourceTags = props.tagWhitelist?.length
    ? props.tagWhitelist
    : Array.from(
        new Set(
          currentOptions.value.flatMap(opt =>
            (opt.tags ?? []).map(tag => (tag ?? '').trim()).filter(Boolean)
          )
        )
      )

  for (const opt of currentOptions.value) {
    for (const tag of opt.tags ?? []) {
      const t = (tag ?? '').trim()
      if (t && sourceTags.includes(t)) hit.add(t)
    }
  }
  return ['全部', ...sourceTags.filter(t => hit.has(t))]
})

const filteredOptions = computed(() => {
  if (props.requireTagToShowOptions && selectedTag.value === '全部') return []
  if (selectedTag.value === '全部') return currentOptions.value
  return currentOptions.value.filter(opt => (opt.tags ?? []).includes(selectedTag.value))
})

watch(
  () => editingSlot.value,
  () => {
    selectedTag.value = '全部'
  }
)

function applyOption(skillId: string) {
  if (editingSlot.value === 'main') {
    emit('update:modelValue', {
      ...props.modelValue,
      mainSkillId: skillId
    })
    return
  }
  if (typeof editingSlot.value !== 'number') return
  const next = [...props.modelValue.supportSkillIds]
  next[editingSlot.value] = skillId
  emit('update:modelValue', {
    ...props.modelValue,
    supportSkillIds: next
  })
}

function clearCurrentSlot() {
  if (editingSlot.value === 'main') {
    emit('update:modelValue', {
      ...props.modelValue,
      mainSkillId: ''
    })
    return
  }
  if (typeof editingSlot.value !== 'number') return
  const next = [...props.modelValue.supportSkillIds]
  next[editingSlot.value] = ''
  emit('update:modelValue', {
    ...props.modelValue,
    supportSkillIds: next
  })
}
</script>

<style scoped>
.skill-card {
  background: #1a1a2e;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  padding: 14px;
}

.skill-card-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.skill-card-title-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.skill-card-title {
  font-size: 15px;
  color: #fff;
  font-weight: 600;
}

.skill-card-role {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 999px;
  border: 1px solid transparent;
}

.role-core {
  color: #facc15;
  background: rgba(250, 204, 21, 0.14);
  border-color: rgba(250, 204, 21, 0.35);
}

.role-active {
  color: #60a5fa;
  background: rgba(96, 165, 250, 0.14);
  border-color: rgba(96, 165, 250, 0.35);
}

.role-passive {
  color: #34d399;
  background: rgba(52, 211, 153, 0.14);
  border-color: rgba(52, 211, 153, 0.35);
}

.skill-card-count {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.link-diagram {
  position: relative;
  height: 300px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: radial-gradient(circle at center, rgba(233, 69, 96, 0.08), rgba(0, 0, 0, 0.2));
  margin-bottom: 10px;
  overflow: hidden;
}

.link-lines {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.node {
  position: absolute;
  transform: translate(-50%, -50%);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(18, 18, 35, 0.95);
  color: #fff;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 8px;
  text-align: center;
  gap: 4px;
}

.node:hover {
  border-color: rgba(233, 69, 96, 0.5);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.16);
}

.node.active {
  border-color: rgba(233, 69, 96, 0.8);
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.24);
}

.node.filled {
  border-color: rgba(52, 211, 153, 0.55);
}

.node-main {
  left: 50%;
  top: 50%;
  width: 170px;
  min-height: 92px;
  z-index: 2;
}

.node-support {
  width: 126px;
  min-height: 76px;
  z-index: 3;
}

.node-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.72);
}

.node-name {
  font-size: 12px;
  line-height: 1.25;
}

.picker-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.22);
  padding: 10px;
}

.picker-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.picker-title {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.82);
}

.picker-clear {
  height: 28px;
  border-radius: 7px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
  padding: 0 10px;
  font-size: 12px;
  cursor: pointer;
}

.picker-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.picker-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag-chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.03);
  color: #fff;
  border-radius: 999px;
  height: 28px;
  padding: 0 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.tag-chip:hover {
  border-color: rgba(233, 69, 96, 0.5);
}

.tag-chip.active {
  border-color: rgba(233, 69, 96, 0.75);
  background: rgba(233, 69, 96, 0.16);
}

.opt-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 8px;
}

.opt-chip {
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.03);
  color: #fff;
  border-radius: 10px;
  min-height: 44px;
  padding: 6px 10px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
  text-align: left;
}

.opt-chip:hover {
  border-color: rgba(233, 69, 96, 0.6);
  background: rgba(233, 69, 96, 0.14);
}

.picker-divider {
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
  margin: 2px 0 4px;
}

.opt-icon {
  width: 28px;
  height: 28px;
  border-radius: 6px;
  object-fit: cover;
  flex-shrink: 0;
}

.opt-name {
  line-height: 1.25;
}
</style>

