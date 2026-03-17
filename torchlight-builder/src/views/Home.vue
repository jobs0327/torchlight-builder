<template>
  <div class="home-page">
    <div class="hero-section">
      <h1 class="title">火炬之光无限</h1>
      <h2 class="subtitle">BD 模拟器</h2>
      <p class="description">
        构建你的角色，优化你的Build，探索无限可能
      </p>
      <div class="actions">
        <router-link to="/talent" class="action-btn primary">
          开始构建
        </router-link>
        <router-link to="/equipment" class="action-btn secondary">
          浏览装备
        </router-link>
      </div>
    </div>

    <div class="features-section">
      <div class="feature-card">
        <div class="feature-icon">🎯</div>
        <h3>天赋模拟</h3>
        <p>可视化天赋树，轻松规划你的天赋点分配</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">⚔️</div>
        <h3>技能搭配</h3>
        <p>组合主动技能与辅助技能，打造独特玩法</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">🎒</div>
        <h3>装备模拟</h3>
        <p>模拟装备属性，计算最终战斗力</p>
      </div>
      <div class="feature-card">
        <div class="feature-icon">📊</div>
        <h3>数据计算</h3>
        <p>精确计算DPS、防御属性和资源消耗</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
</script>

<style scoped>
.home-page {
  min-height: calc(100vh - 60px);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.hero-section {
  text-align: center;
  margin-bottom: 4rem;
}

.title {
  font-size: 3rem;
  background: linear-gradient(135deg, #e94560, #f97316);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin-bottom: 0.5rem;
}

.subtitle {
  font-size: 1.5rem;
  color: #a0a0a0;
  font-weight: normal;
  margin-bottom: 1rem;
}

.description {
  color: #666;
  font-size: 1.125rem;
  margin-bottom: 2rem;
}

.actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
}

.action-btn {
  padding: 0.875rem 2rem;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.3s ease;
}

.action-btn.primary {
  background: linear-gradient(135deg, #e94560 0%, #0f3460 100%);
  color: #fff;
}

.action-btn.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(233, 69, 96, 0.4);
}

.action-btn.secondary {
  background: transparent;
  border: 1px solid var(--border-color);
  color: #a0a0a0;
}

.action-btn.secondary:hover {
  border-color: var(--primary-color);
  color: #fff;
}

.features-section {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1.5rem;
  max-width: 1000px;
}

.feature-card {
  background: #1a1a2e;
  border: 1px solid var(--border-color);
  border-radius: 12px;
  padding: 1.5rem;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  border-color: var(--primary-color);
  transform: translateY(-4px);
}

.feature-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.feature-card h3 {
  color: #fff;
  margin-bottom: 0.5rem;
}

.feature-card p {
  color: #666;
  font-size: 0.875rem;
  line-height: 1.5;
}

@media (max-width: 768px) {
  .features-section {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
