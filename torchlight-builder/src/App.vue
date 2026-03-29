<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">
        <h1>火炬之光无限 - BD模拟器</h1>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/hero" class="nav-link">英雄</router-link>
        <router-link to="/talent" class="nav-link">天赋</router-link>
        <router-link to="/skills" class="nav-link">技能</router-link>
        <router-link to="/equipment" class="nav-link">装备</router-link>
        <router-link to="/pactspirit" class="nav-link">契灵</router-link>
        <router-link to="/hero-memories" class="nav-link">追忆</router-link>
        <router-link to="/build-calc" class="nav-link">数据计算</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { watch } from 'vue'
import { useBuildStore } from '@/stores/build'
import { useTalentStore } from '@/stores/talent'
import { useProfessionTalentStore } from '@/stores/professionTalent'

const buildStore = useBuildStore()
const talentStore = useTalentStore()
const professionStore = useProfessionTalentStore()

function syncTalentIntoBuild() {
  buildStore.setTalent({
    nodeIds: Array.from(talentStore.allocatedNodes),
    profession: professionStore.trees.map(t => ({
      treeId: t.id,
      allocatedPoints: t.allocatedPoints,
      selected: !!t.isSelected
    })),
    professionTreesFull: JSON.parse(JSON.stringify(professionStore.trees))
  })
}

watch(
  () =>
    `${Array.from(talentStore.allocatedNodes)
      .sort()
      .join(',')}|${JSON.stringify(
      professionStore.trees.map(t => ({
        id: t.id,
        ap: t.allocatedPoints,
        sel: t.isSelected,
        n: t.nodes.map(x => [x.id, x.currentPoints]),
        c: t.coreTalents.map(x => [x.id, x.currentPoints])
      }))
    )}`,
  syncTalentIntoBuild,
  { immediate: true }
)
</script>

<style scoped>
.app-container {
  height: 100vh;
  height: 100dvh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  /** 供子页面 calc(100dvh - var) 对齐主内容可视区 */
  --app-header-height: 4.75rem;
}

.app-header {
  flex-shrink: 0;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 2px solid #e94560;
}

.logo h1 {
  color: #fff;
  font-size: 1.25rem;
  margin: 0;
}

.nav-menu {
  display: flex;
  gap: 1rem;
}

.nav-link {
  color: #a0a0a0;
  text-decoration: none;
  padding: 0.4rem 0.8rem;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-size: 0.9rem;
}

.nav-link:hover,
.nav-link.router-link-active {
  color: #fff;
  background: rgba(233, 69, 96, 0.2);
}

.app-main {
  flex: 1;
  min-height: 0;
  background: #0f0f1a;
  overflow-y: auto;
  overflow-x: hidden;
}
</style>
