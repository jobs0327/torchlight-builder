<template>
  <div class="talent-panel-selector">
    <div class="panel-tabs">
      <button
        v-for="panel in panels"
        :key="panel.id"
        :class="['panel-tab', { active: activePanelId === panel.id }]"
        @click="$emit('select', panel.id)"
      >
        {{ panel.name }}
      </button>
    </div>

    <div class="god-selector">
      <button
        v-for="god in godTypes"
        :key="god"
        :class="['god-btn', { active: activeGodType === god }]"
        :style="{ '--god-color': GOD_COLORS[god] }"
        @click="$emit('selectGod', god)"
      >
        <span class="god-icon">{{ godIcons[god] }}</span>
        <span class="god-name">{{ GOD_NAMES[god] }}</span>
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { TalentPanel, GodType } from '@/types'
import { GOD_COLORS, GOD_NAMES } from '@/types'

interface Props {
  panels: TalentPanel[]
  activePanelId: string
  activeGodType: GodType
}

defineProps<Props>()

defineEmits<{
  (e: 'select', panelId: string): void
  (e: 'selectGod', godType: GodType): void
}>()

const godTypes: GodType[] = ['strength', 'dexterity', 'intelligence', 'war', 'trickery', 'machine']

const godIcons: Record<GodType, string> = {
  strength: '💪',
  dexterity: '🏹',
  intelligence: '📚',
  war: '⚔️',
  trickery: '🎭',
  machine: '⚙️'
}
</script>

<style scoped>
.talent-panel-selector {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  padding: 1rem;
  background: #1a1a2e;
  border-radius: 8px;
}

.panel-tabs {
  display: flex;
  gap: 0.5rem;
}

.panel-tab {
  flex: 1;
  padding: 0.75rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: #a0a0a0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.panel-tab:hover {
  border-color: var(--primary-color);
  color: #fff;
}

.panel-tab.active {
  background: var(--primary-color);
  border-color: var(--primary-color);
  color: #fff;
}

.god-selector {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 0.5rem;
}

.god-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.25rem;
  padding: 0.75rem 0.5rem;
  background: transparent;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  color: #a0a0a0;
  cursor: pointer;
  transition: all 0.3s ease;
}

.god-btn:hover {
  border-color: var(--god-color);
  color: #fff;
}

.god-btn.active {
  background: color-mix(in srgb, var(--god-color) 20%, transparent);
  border-color: var(--god-color);
  color: var(--god-color);
}

.god-icon {
  font-size: 1.5rem;
}

.god-name {
  font-size: 0.75rem;
}
</style>
