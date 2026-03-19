<template>
  <div class="talent-page">
    <ToastMessage :message="professionStore.toastMessage" type="warning" />
    <ConfirmDialog
      v-model="showClearConfirm"
      title="提示"
      message="当前天赋已有天赋被选择，是否要清空？"
      cancel-text="取消"
      confirm-text="确认"
      @confirm="onConfirmClearAndDeselect"
      @cancel="onCancelClear"
    />
    <div class="talent-sidebar">
      <div class="nav-section">
        <button
          class="nav-item"
          :class="{ active: activeNav === 'overview' }"
          @click="activeNav = 'overview'"
        >
          总览
        </button>
        <!-- <button
          v-for="god in godOrder"
          :key="god"
          class="nav-item"
          :class="{ active: activeNav === god }"
          @click="selectGod(god)"
        >
          {{ GOD_NAMES[god] }}
        </button> -->
      </div>

      <!-- <div class="panel-section" v-if="activeNav !== 'overview'">
        <div class="panel-section-header">
          <div class="panel-god-icon" v-if="activeGodType">
            <span class="god-icon">{{ godIcons[activeGodType] }}</span>
          </div>
          <div class="panel-god-info" v-if="activeGodType">
            <div class="panel-god-name">{{ GOD_NAMES[activeGodType] }}</div>
            <div class="panel-god-tip">选择一个天赋面板进入加点</div>
          </div>
        </div>

        <div v-if="panelsForActiveGod.length" class="panel-list">
          <div
            v-for="panel in panelsForActiveGod"
            :key="panel.id"
            class="panel-item"
            :class="{ active: !!panel.isSelected }"
            @click="selectPanel(panel.id)"
          >
            <div class="panel-icon" :style="{ borderColor: GOD_COLORS[panel.godType] }">
              {{ panel.name.charAt(0) }}
            </div>
            <div class="panel-info">
              <span class="panel-name">{{ panel.name }}</span>
            </div>
          </div>
        </div>

        <div v-else class="panel-empty">
          该神格暂时没有可用的天赋面板
        </div>
      </div> -->

      <div class="allocated-effects">
        <h3 class="sidebar-title">已分配效果</h3>
        <div class="effects-list" v-if="allocatedEffects.length > 0">
          <div
            v-for="(effect, index) in allocatedEffects"
            :key="index"
            class="effect-item"
          >
            {{ effect }}
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧：神格总览 + 当前天赋树 -->
    <div class="talent-main">
      <div class="god-overview" v-if="activeNav === 'overview'">
        <div
          v-for="god in godOrder"
          :key="god"
          class="god-card"
          :style="{ '--god-color': GOD_COLORS[god] }"
        >
          <div class="god-card-header">
            <div class="god-card-title">{{ GOD_NAMES[god] }}</div>
          </div>
          <div class="god-card-body">
            <button
              v-for="tree in treesByGod[god] || []"
              :key="tree.id"
              class="god-panel-btn"
              :class="{ active: !!tree.isSelected }"
              @click="selectPanel(tree.id)"
            >
              <span class="god-panel-name">{{ tree.name }}</span>
              <button
                v-if="tree.isSelected"
                type="button"
                class="god-panel-close"
                title="取消选中"
                @click.stop="onDeselectPanel(tree.id)"
              >
                ×
              </button>
            </button>
          </div>
        </div>
      </div>

      <div class="talent-tree-container">
        <ProfessionTalentTree
          v-if="professionStore.activeTree"
          :tree="professionStore.activeTree"
          @allocate="onAllocate"
          @deallocate="onDeallocate"
          @reset="onReset"
          @close="onCloseActiveTree"
        />
        <div v-else class="no-tree">
          <p>请选择一个天赋面板</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useProfessionTalentStore } from '@/stores/professionTalent'
import ProfessionTalentTree from '@/components/talent/ProfessionTalentTree.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import ToastMessage from '@/components/ui/ToastMessage.vue'
import { GOD_COLORS, GOD_NAMES, type GodType } from '@/types'

const professionStore = useProfessionTalentStore()

const allocatedEffects = computed(() => professionStore.getAllocatedEffects())

const godOrder: GodType[] = [
  'strength',
  'dexterity',
  'intelligence',
  'war',
  'trickery',
  'machine',
]

type NavKey = 'overview' | GodType
const activeNav = ref<NavKey>('overview')

const activeGodType = computed<GodType | null>(() => {
  return activeNav.value === 'overview' ? null : (activeNav.value as GodType)
})

const godIcons: Record<GodType, string> = {
  strength: '💪',
  dexterity: '🏹',
  intelligence: '📚',
  war: '⚔️',
  trickery: '🎭',
  machine: '⚙️',
}

const treesByGod = computed(() => {
  const map: Record<GodType, typeof professionStore.trees> = {
    strength: [],
    dexterity: [],
    intelligence: [],
    war: [],
    trickery: [],
    machine: [],
  }
  for (const tree of professionStore.trees) {
    map[tree.godType].push(tree)
  }
  return map
})

const panelsForActiveGod = computed(() => {
  if (activeNav.value === 'overview') return []
  const god = activeNav.value as GodType
  return treesByGod.value[god] || []
})

function selectGod(god: GodType) {
  activeNav.value = god
}

function selectPanel(treeId: string) {
  professionStore.setActiveTree(treeId)
}

const showClearConfirm = ref(false)
const pendingCancelTreeId = ref<string>('')

function onCloseActiveTree() {
  const treeId = professionStore.activeTree?.id
  if (!treeId) return
  const result = professionStore.deselectTree(treeId)
  if (result === 'NEED_CONFIRM_CLEAR') {
    pendingCancelTreeId.value = treeId
    showClearConfirm.value = true
  }
}

function onDeselectPanel(treeId: string) {
  const result = professionStore.deselectTree(treeId)
  if (result === 'NEED_CONFIRM_CLEAR') {
    pendingCancelTreeId.value = treeId
    showClearConfirm.value = true
  }
}

function onConfirmClearAndDeselect() {
  const treeId = pendingCancelTreeId.value
  if (!treeId) return
  professionStore.resetTree(treeId)
  // 清空后再取消高亮
  professionStore.deselectTree(treeId)
  pendingCancelTreeId.value = ''
}

function onCancelClear() {
  pendingCancelTreeId.value = ''
}

function onAllocate(nodeId: string) {
  professionStore.allocateNode(nodeId)
}

function onDeallocate(nodeId: string) {
  professionStore.deallocateNode(nodeId)
}

function onReset() {
  professionStore.resetTree()
}
</script>

<style scoped>
.talent-page {
  display: flex;
  height: 100vh;
  background: #0f0f1a;
}

.talent-sidebar {
  width: 260px;
  background: rgba(0, 0, 0, 0.3);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  padding: 12px 8px;
  gap: 12px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.nav-item {
  border: none;
  outline: none;
  background: transparent;
  color: #cbd5f5;
  padding: 8px 10px;
  text-align: left;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  font-size: 13px;
}

.nav-item.active {
  background: rgba(255, 255, 255, 0.12);
  color: #ffffff;
}

.panel-section {
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  padding-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  max-height: 50vh;
  overflow-y: auto;
}

.panel-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 4px 4px;
}

.panel-god-icon {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-god-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-god-name {
  font-size: 13px;
  color: #ffffff;
}

.panel-god-tip {
  font-size: 11px;
  color: #9ca3af;
}

.panel-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.panel-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.panel-item:hover {
  background: rgba(255, 255, 255, 0.08);
}

.panel-item.active {
  background: rgba(233, 69, 96, 0.26);
  border: 1px solid rgba(233, 69, 96, 0.6);
}

.panel-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  border: 2px solid #3a3a5a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: bold;
  color: #fff;
  background: rgba(0, 0, 0, 0.3);
}

.panel-info {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.panel-name {
  font-size: 13px;
  color: #fff;
}

.panel-points {
  font-size: 11px;
  color: #ffd700;
}

.panel-empty {
  padding: 8px 4px;
  font-size: 12px;
  color: #6b7280;
}

.sidebar-title {
  font-size: 14px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 8px 0;
  padding-bottom: 4px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.allocated-effects {
  flex: 1;
  padding-top: 8px;
  overflow-y: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.effect-item {
  padding: 6px 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 12px;
  color: #ccc;
  line-height: 1.4;
}

.talent-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.god-overview {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  gap: 16px;
  padding: 20px 24px 0;
}

.god-card {
  width: 180px;
  background: rgba(15, 23, 42, 0.9);
  border-radius: 10px;
  padding: 12px 10px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.4);
}

.god-card-header {
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.god-card-title {
  font-size: 14px;
  color: #e5e7eb;
  text-align: center;
}

.god-card-body {
  margin-top: 8px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.god-panel-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  padding: 6px 4px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.1);
  cursor: pointer;
  transition: all 0.2s ease;
  color: #e5e7eb;
  font-size: 12px;
  position: relative;
}

.god-panel-btn.active {
  border-color: var(--god-color);
  box-shadow: 0 0 10px color-mix(in srgb, var(--god-color) 60%, transparent);
  background: color-mix(in srgb, var(--god-color) 18%, rgba(0, 0, 0, 0.3));
}

.god-panel-name {
  font-size: 12px;
  padding-right: 16px;
}

.god-panel-close {
  position: absolute;
  top: 50%;
  right: 6px;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  border-radius: 6px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 14px;
  padding: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.god-panel-close:hover {
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
}

.god-panel-points {
  font-size: 11px;
  color: #facc15;
}

.talent-tree-container {
  flex: 1;
  position: relative;
  overflow: hidden;
}

.no-tree {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #666;
  font-size: 16px;
}
</style>
