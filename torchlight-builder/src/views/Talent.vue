<template>
  <div class="talent-page">
    <div class="talent-sidebar">
      <div class="profession-selector">
        <h3 class="sidebar-title">职业天赋</h3>
        <div class="profession-list">
          <div
            v-for="tree in professionStore.trees"
            :key="tree.id"
            :class="['profession-item', { active: professionStore.activeTreeId === tree.id }]"
            @click="selectProfession(tree.id)"
          >
            <div class="profession-icon" :style="{ borderColor: GOD_COLORS[tree.godType] }">
              {{ tree.name.charAt(0) }}
            </div>
            <div class="profession-info">
              <span class="profession-name">{{ tree.name }}</span>
              <span class="profession-points">{{ tree.allocatedPoints }}/{{ tree.totalPoints }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="allocated-effects" v-if="allocatedEffects.length > 0">
        <h3 class="sidebar-title">已分配效果</h3>
        <div class="effects-list">
          <div v-for="(effect, index) in allocatedEffects" :key="index" class="effect-item">
            {{ effect }}
          </div>
        </div>
      </div>
    </div>

    <div class="talent-main">
      <ProfessionTalentTree
        v-if="professionStore.activeTree"
        :tree="professionStore.activeTree"
        @allocate="onAllocate"
        @deallocate="onDeallocate"
        @reset="onReset"
      />
      <div v-else class="no-tree">
        <p>请选择一个职业天赋树</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useProfessionTalentStore } from '@/stores/professionTalent'
import ProfessionTalentTree from '@/components/talent/ProfessionTalentTree.vue'
import { GOD_COLORS } from '@/types'

const professionStore = useProfessionTalentStore()

const allocatedEffects = computed(() => professionStore.getAllocatedEffects())

function selectProfession(treeId: string) {
  professionStore.setActiveTree(treeId)
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
  width: 280px;
  background: rgba(0, 0, 0, 0.3);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-title {
  font-size: 14px;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 1px;
  margin: 0 0 16px 0;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.profession-selector {
  padding: 20px;
}

.profession-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.profession-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.profession-item:hover {
  background: rgba(255, 255, 255, 0.1);
}

.profession-item.active {
  background: rgba(233, 69, 96, 0.2);
  border: 1px solid rgba(233, 69, 96, 0.5);
}

.profession-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 2px solid #3a3a5a;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  font-weight: bold;
  color: #fff;
  background: rgba(0, 0, 0, 0.3);
}

.profession-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.profession-name {
  font-size: 14px;
  color: #fff;
  font-weight: 500;
}

.profession-points {
  font-size: 12px;
  color: #ffd700;
}

.allocated-effects {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.effects-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.effect-item {
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 4px;
  font-size: 12px;
  color: #ccc;
  line-height: 1.4;
}

.talent-main {
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
