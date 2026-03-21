<template>
  <div class="skills-page">
    <div class="skills-header">
      <h1>技能模块</h1>
      <p>
        当前 BD 技能构成：<strong>1 个核心技能 + 4 个主动技能 + 4 个被动技能</strong>，每个技能可连接
        <strong>5 个辅助技能</strong>。
      </p>
    </div>

    <div class="skills-summary">
      <div class="summary-item">
        <span class="summary-label">技能位总数</span>
        <span class="summary-value">9</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">已选择技能</span>
        <span class="summary-value">{{ selectedMainCount }}/9</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">已连接辅助</span>
        <span class="summary-value">{{ selectedSupportCount }}/45</span>
      </div>
    </div>

    <div class="skills-layout">
      <aside class="skills-left">
        <section class="slot-section">
          <h2>核心技能</h2>
          <button
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'core' }"
            @click="selectSlot('core', 0)"
          >
            <span class="slot-title">核心技能槽位</span>
            <span class="slot-name">{{ getSkillDisplayName(coreSkill.mainSkillId, activeSkillOptions) || '未选择' }}</span>
          </button>
        </section>

        <section class="slot-section">
          <h2>主动技能</h2>
          <button
            v-for="(item, idx) in activeSkills"
            :key="`active-list-${idx}`"
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'active' && selectedSlot.index === idx }"
            @click="selectSlot('active', idx)"
          >
            <span class="slot-title">主动技能 {{ idx + 1 }}</span>
            <span class="slot-name">{{ getSkillDisplayName(item.mainSkillId, activeSkillOptions) || '未选择' }}</span>
          </button>
        </section>

        <section class="slot-section">
          <h2>被动技能</h2>
          <button
            v-for="(item, idx) in passiveSkills"
            :key="`passive-list-${idx}`"
            type="button"
            class="slot-item"
            :class="{ active: selectedSlot.role === 'passive' && selectedSlot.index === idx }"
            @click="selectSlot('passive', idx)"
          >
            <span class="slot-title">被动技能 {{ idx + 1 }}</span>
            <span class="slot-name">{{ getSkillDisplayName(item.mainSkillId, passiveSkillOptions) || '未选择' }}</span>
          </button>
        </section>
      </aside>

      <section class="skills-right">
        <h2 class="panel-title">{{ selectedPanelTitle }}</h2>

        <SkillLinkCard
          v-if="selectedSlot.role === 'core'"
          title="核心技能"
          role="core"
          :model-value="coreSkill"
          @update:model-value="coreSkill = $event"
          :main-options="activeSkillOptions"
          :support-options="supportSkillOptions"
          :tag-whitelist="activeSkillTags"
          :require-tag-to-show-options="true"
        />

        <SkillLinkCard
          v-else-if="selectedSlot.role === 'active'"
          :title="`主动技能 ${selectedSlot.index + 1}`"
          role="active"
          :model-value="activeSkills[selectedSlot.index]"
          @update:model-value="activeSkills[selectedSlot.index] = $event"
          :main-options="activeSkillOptions"
          :support-options="supportSkillOptions"
          :tag-whitelist="activeSkillTags"
          :require-tag-to-show-options="true"
        />

        <SkillLinkCard
          v-else
          :title="`被动技能 ${selectedSlot.index + 1}`"
          role="passive"
          :model-value="passiveSkills[selectedSlot.index]"
          @update:model-value="passiveSkills[selectedSlot.index] = $event"
          :main-options="passiveSkillOptions"
          :support-options="supportSkillOptions"
        />
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import SkillLinkCard from '@/components/skills/SkillLinkCard.vue'
import activeSkillTagsData from '@/data/skills/activeSkillTags.json'

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

type SlotRole = 'core' | 'active' | 'passive'

const activeSkillTags: string[] = activeSkillTagsData.tags ?? []
const activeSkillOptionsFromData: SkillOption[] = (activeSkillTagsData.activeSkills ?? []).map(item => ({
  id: String(item.id ?? ''),
  name: String(item.name ?? ''),
  iconUrl: item.localIconUrl ? String(item.localIconUrl) : item.iconUrl ? String(item.iconUrl) : '',
  tags: Array.isArray(item.tags) ? item.tags.map(tag => String(tag)) : []
}))

function createEmptySkillLink(): SkillLinkItem {
  return {
    mainSkillId: '',
    supportSkillIds: ['', '', '', '', '']
  }
}

const coreSkill = ref<SkillLinkItem>(createEmptySkillLink())
const activeSkills = ref<SkillLinkItem[]>(Array.from({ length: 4 }, createEmptySkillLink))
const passiveSkills = ref<SkillLinkItem[]>(Array.from({ length: 4 }, createEmptySkillLink))
const selectedSlot = ref<{ role: SlotRole; index: number }>({ role: 'core', index: 0 })

const activeSkillOptions: SkillOption[] = activeSkillOptionsFromData

const passiveSkillOptions: SkillOption[] = [
  { id: 'passive_sharp', name: '锐利本能', tags: ['被动', '攻击'] },
  { id: 'passive_focus', name: '专注施法', tags: ['被动', '法术'] },
  { id: 'passive_overload', name: '元素超载', tags: ['被动', '法术', '触发'] },
  { id: 'passive_survival', name: '生存意志', tags: ['被动', '防护'] },
  { id: 'passive_frenzy', name: '狂热追击', tags: ['被动', '增益'] }
]

const supportSkillOptions: SkillOption[] = [
  { id: 'sup_rapid', name: '快速施放', tags: ['辅助技能', '法术', '攻击'] },
  { id: 'sup_penetrate', name: '元素穿透', tags: ['辅助技能', '法术', '投射物'] },
  { id: 'sup_crit', name: '暴击强化', tags: ['辅助技能', '攻击', '法术'] },
  { id: 'sup_chain', name: '连锁扩散', tags: ['辅助技能', '法术', '投射物'] },
  { id: 'sup_duration', name: '持续增幅', tags: ['辅助技能', '持续'] },
  { id: 'sup_costdown', name: '消耗抑制', tags: ['辅助技能', '魔力封印', '生命封印'] },
  { id: 'sup_haste', name: '高效节奏', tags: ['辅助技能', '增益', '触发'] }
]

const allSkillNodes = computed(() => [coreSkill.value, ...activeSkills.value, ...passiveSkills.value])

const selectedMainCount = computed(
  () => allSkillNodes.value.filter(item => item.mainSkillId.trim().length > 0).length
)

const selectedSupportCount = computed(() =>
  allSkillNodes.value.reduce(
    (sum, item) => sum + item.supportSkillIds.filter(v => v.trim().length > 0).length,
    0
  )
)

const selectedPanelTitle = computed(() => {
  if (selectedSlot.value.role === 'core') return '核心技能详情'
  if (selectedSlot.value.role === 'active') return `主动技能 ${selectedSlot.value.index + 1} 详情`
  return `被动技能 ${selectedSlot.value.index + 1} 详情`
})

function selectSlot(role: SlotRole, index: number) {
  selectedSlot.value = { role, index }
}

function getSkillDisplayName(skillId: string, options: SkillOption[]) {
  const hit = options.find(o => o.id === skillId)
  return hit?.name ?? ''
}
</script>

<style scoped>
.skills-page {
  padding: 18px;
  color: #fff;
}

.skills-header {
  margin-bottom: 14px;
}

.skills-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.skills-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.74);
}

.skills-summary {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
}

.summary-item {
  background: rgba(0, 0, 0, 0.24);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  padding: 10px 12px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-label {
  font-size: 13px;
  color: rgba(255, 255, 255, 0.72);
}

.summary-value {
  font-size: 16px;
  font-weight: 700;
  color: #e94560;
}

.skills-layout {
  display: grid;
  grid-template-columns: 340px minmax(0, 1fr);
  gap: 12px;
}

.skills-left {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.22);
  padding: 10px;
  max-height: calc(100vh - 220px);
  overflow-y: auto;
}

.slot-section + .slot-section {
  margin-top: 12px;
}

.slot-section h2 {
  margin: 0 0 8px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.88);
}

.slot-item {
  width: 100%;
  text-align: left;
  display: flex;
  flex-direction: column;
  gap: 3px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 9px;
  padding: 10px;
  color: #fff;
  cursor: pointer;
}

.slot-item + .slot-item {
  margin-top: 8px;
}

.slot-item:hover {
  border-color: rgba(233, 69, 96, 0.4);
}

.slot-item.active {
  border-color: rgba(233, 69, 96, 0.8);
  box-shadow: inset 0 0 0 1px rgba(233, 69, 96, 0.22);
  background: rgba(233, 69, 96, 0.08);
}

.slot-title {
  font-size: 13px;
}

.slot-name {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
}

.skills-right {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
  padding: 10px;
}

.panel-title {
  margin: 0 0 10px;
  font-size: 15px;
  color: #f3f4f6;
}

@media (max-width: 1100px) {
  .skills-summary {
    grid-template-columns: 1fr;
  }

  .skills-layout {
    grid-template-columns: 1fr;
  }

  .skills-left {
    max-height: none;
  }
}
</style>
