<template>
  <div class="app-container">
    <header class="app-header">
      <div class="logo">
        <h1>火炬之光无限 - BD模拟器</h1>
      </div>
      <nav class="nav-menu">
        <router-link to="/" class="nav-link">首页</router-link>
        <router-link to="/talent" class="nav-link">天赋</router-link>
        <router-link to="/skills" class="nav-link">技能</router-link>
        <router-link to="/equipment" class="nav-link">装备</router-link>
      </nav>
    </header>
    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.app-container {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
  background: #0f0f1a;
  overflow: hidden;
}
</style>
