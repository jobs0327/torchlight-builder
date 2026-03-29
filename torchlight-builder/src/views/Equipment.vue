<template>
  <div class="equipment-page">
    <div class="equipment-header">
      <h1>装备模块</h1>
      <p>
        请先在右侧面板顶部选择 <strong>暗金</strong> 或 <strong>自制</strong>，再使用左侧 <strong>10</strong> 个装备位与右侧列表；已穿戴格子的右上角 <strong>×</strong> 可卸下。
      </p>
    </div>

    <div class="equipment-summary">
      <div class="summary-item">
        <span class="summary-label">已装备</span>
        <span class="summary-value">{{ equippedCount }}/10</span>
      </div>
      <div class="summary-item">
        <span class="summary-label">当前部位</span>
        <span class="summary-value summary-value--muted">{{ activeSlot.label }}</span>
      </div>
    </div>
    <details class="persist-debug-panel">
      <summary>持久化调试（定位写入/读取）</summary>
      <div class="persist-debug-grid">
        <div>最近写入结果</div>
        <div>{{ persistenceDebug.lastWriteStatus }}</div>
        <div>最近写入时间</div>
        <div>{{ persistenceDebug.lastWriteAtText || '-' }}</div>
        <div>最近读取来源</div>
        <div>{{ persistenceDebug.lastReadSource || '-' }}</div>
        <div>最近读取时间</div>
        <div>{{ persistenceDebug.lastReadAtText || '-' }}</div>
        <div>恢复后装备数量</div>
        <div>{{ persistenceDebug.lastAppliedEquippedCount }}</div>
        <div>standalone payload 长度</div>
        <div>{{ persistenceDebug.standalonePayloadSize }}</div>
        <div>build fallback payload 长度</div>
        <div>{{ persistenceDebug.buildFallbackPayloadSize }}</div>
      </div>
    </details>

    <div class="equipment-layout">
      <aside
        class="equipment-slots-panel"
        :class="{ 'equipment-slots-panel--locked': !equipmentUiUnlocked }"
        aria-label="装备格子"
      >
        <h2 class="panel-section-title">装备栏</h2>
        <div class="equipment-slots-grid">
          <div
            v-for="(slot, index) in EQUIPMENT_SLOTS"
            :key="slot.id"
            class="equipment-slot-cell"
          >
            <button
              type="button"
              class="equipment-slot"
              :class="{
                active: selectedSlotIndex === index,
                filled: !!equipped[index],
                'equipment-slot--off-blocked':
                  slot.id === 'weapon_off' && equippedMainIsTwoHanded
              }"
              :title="
                slot.id === 'weapon_off' && equippedMainIsTwoHanded
                  ? '主手为双手武器时无法装备副武器'
                  : undefined
              "
              @click="selectedSlotIndex = index"
            >
              <span class="equipment-slot-icon-wrap" :class="{ 'equipment-slot-icon-wrap--empty': !equipped[index] }">
                <img
                  v-if="equipped[index]?.iconUrl"
                  :src="equipped[index]!.iconUrl"
                  class="equipment-slot-thumb"
                  alt=""
                />
                <span v-else class="equipment-slot-placeholder" aria-hidden="true" />
              </span>
              <span class="equipment-slot-text">
                <span class="equipment-slot-title">{{ slot.label }}</span>
                <span class="equipment-slot-name">{{
                  equipped[index]?.name || '未装备'
                }}</span>
              </span>
            </button>
            <button
              v-if="equipped[index]"
              type="button"
              class="equipment-slot-unmount"
              aria-label="卸下该部位装备"
              title="卸下"
              @click.stop="clearSlotAt(index)"
            >
              ×
            </button>
          </div>
        </div>

        <section class="equipment-effects" aria-label="已选效果">
          <h2 class="panel-section-title">已选效果</h2>
          <p v-if="equippedEffectsBlocks.length === 0" class="equipment-effects-empty">
            <template v-if="equipmentKind === 'crafted'">
              暂无已记录的自制装备。请在右侧选择打造基底，选择后即可在装备栏与本列表中看到该部位（无需先点词缀）。
            </template>
            <template v-else>
              尚未穿戴装备。词条来自本地数据中的 <code>effectLines</code>，可运行
              <code>npm run sync:legendary-gear-effects</code> 从 TLIDB 补全。
            </template>
          </p>
          <div v-else class="equipment-effects-stack">
            <article
              v-for="block in equippedEffectsBlocks"
              :key="`${block.slotIndex}-${block.itemId}`"
              class="equipment-effect-card"
            >
              <header class="equipment-effect-card-head">
                <span class="equipment-effect-slot">{{ block.slotLabel }}</span>
                <span class="equipment-effect-name">{{ block.itemName }}</span>
              </header>
              <ul v-if="block.lines.length" class="equipment-effect-lines">
                <li
                  v-for="(line, i) in block.lines"
                  :key="i"
                  class="equipment-effect-line-row"
                  :class="{ 'equipment-effect-line--flavor': isFlavorEffectLine(line) }"
                >
                  <div class="equipment-effect-line-main">
                    <template v-if="isFlavorEffectLine(line)">{{ line }}</template>
                    <EffectLineRollPicker
                      v-else
                      :line="line"
                      :pick-key-prefix="`${block.slotIndex}|${block.itemId}|${i}`"
                      :selections="effectRollSelections"
                      @set-pick="onEffectRollPick"
                    />
                  </div>
                  <button
                    v-if="block.craftedLineRemoveMeta?.[i]"
                    type="button"
                    class="equipment-effect-line-unmount"
                    aria-label="移除此词条"
                    title="移除此词条"
                    @click.stop="removeCraftedEquippedAffix(block.slotIndex, block.craftedLineRemoveMeta[i]!)"
                  >
                    ×
                  </button>
                </li>
              </ul>
              <p v-else-if="block.blockKind === 'crafted'" class="equipment-effects-crafted-hint">
                尚未选择词缀，请在右侧列表中点选加入；移除词条请点词条右侧的 ×。
              </p>
              <p v-else class="equipment-effects-missing">该装备暂无词条文本（需同步详情数据）。</p>
            </article>
          </div>
        </section>
      </aside>

      <section class="equipment-picker-panel" aria-label="装备选择">
        <div
          class="equipment-kind-bar"
          role="radiogroup"
          aria-label="装备类型"
        >
          <span class="equipment-kind-label">装备类型</span>
          <div class="equipment-kind-tabs">
            <button
              type="button"
              role="radio"
              class="equipment-kind-tab"
              :class="{ active: equipmentKind === 'legendary' }"
              :aria-checked="equipmentKind === 'legendary'"
              @click="equipmentKind = 'legendary'"
            >
              暗金
            </button>
            <button
              type="button"
              role="radio"
              class="equipment-kind-tab"
              :class="{ active: equipmentKind === 'crafted' }"
              :aria-checked="equipmentKind === 'crafted'"
              @click="equipmentKind = 'crafted'"
            >
              自制
            </button>
          </div>
        </div>

        <template v-if="!equipmentUiUnlocked">
          <h2 class="panel-title">选择装备</h2>
          <p class="picker-mode-hint">
            请先在上方选择 <strong>暗金</strong> 或 <strong>自制</strong>，即可使用左侧装备位与下方筛选标签。
          </p>
        </template>

        <template v-else-if="equipmentKind === 'crafted'">
          <div class="panel-title-row panel-title-row--crafted">
            <h2 class="panel-title panel-title--crafted-heading">自制词缀 · {{ activeSlot.label }}</h2>
            <div class="picker-crafted-rules-hover picker-crafted-rules-hover--in-title">
              <button
                type="button"
                class="picker-crafted-rules-icon-btn"
                aria-label="打造规则说明（悬停或聚焦查看）"
                aria-describedby="picker-crafted-rules-tooltip-panel"
              >
                <svg
                  class="picker-crafted-rules-icon-svg"
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  width="20"
                  height="20"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="16" x2="12" y2="12" />
                  <line x1="12" y1="8" x2="12.01" y2="8" />
                </svg>
              </button>
              <div
                id="picker-crafted-rules-tooltip-panel"
                class="picker-crafted-rules-tooltip"
                role="tooltip"
              >
                <p class="picker-crafted-rules-tooltip-p">
                  打造规则：除六槽外，可选至多 <strong>2</strong> 条基础词缀、<strong>1</strong> 条梦语词缀（数据中为美梦词缀）；主手 / 副手为<strong>武器</strong>（非盾牌）时另可选至多
                  <strong>1</strong> 条<strong>高塔序列</strong>（中阶或高阶，与上述槽位独立，数据见
                  <a
                    class="picker-hint-link"
                    href="https://tlidb.com/cn/TOWER_Sequence"
                    target="_blank"
                    rel="noopener noreferrer"
                  >TLIDB 高塔序列</a>）。六槽为最多
                  <strong>3</strong> 前缀 + <strong>3</strong> 后缀（初阶 / 进阶 / 至臻），至臻与进阶各至多 <strong>2</strong> 条。左侧已选效果顺序为：基底 → 基础 → 梦语 → 高塔序列 →
                  六槽词缀。在右侧列表点选加入；移除请在左侧对应词条旁点击 ×。侵蚀基底等其它类型不占槽，请仅作参考。
                </p>
              </div>
            </div>
          </div>
          <!-- <p class="picker-hint picker-hint--crafted">
            词缀来自本地 <code>craftedAffixes</code>；<strong>基底装备</strong>来自 TLIDB 各子类页「Item」分栏（与
            <a
              class="picker-hint-link"
              href="https://tlidb.com/cn/STR_Helmet#Item"
              target="_blank"
              rel="noopener noreferrer"
            >力量头部 Item</a>
            同源），由 <code>npm run sync:crafted-gear-bases</code> 同步列表，<code>npm run sync:crafted-gear-bases-icons</code> 将图标下载到 <code>public/assets/equipment/crafted-bases</code> 并本地化。<strong>头部 / 上衣 / 手套 / 鞋子</strong>须先选 <strong>主属性（力量、敏捷、智慧）</strong>；<strong>戒指位</strong>须先选 <strong>戒指 / 灵戒</strong>；<strong>主副武器</strong>须先选 <strong>武器类型</strong>，再选打造基底，最后筛选词缀类型（<strong>基础</strong> 与 <strong>初阶 / 进阶 / 至臻</strong> 等）；选「全部类型」时另含侵蚀基底、美梦等。
          </p> -->
          <p
            v-if="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
            class="picker-blocked-hint"
          >
            当前主手为双手武器时无法为副手选择词缀；请先更换主手或卸下双手武器。
          </p>

          <template
            v-if="
              equipmentKind === 'crafted' &&
              !(activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded)
            "
          >
            <div
              v-if="showCraftedArmorPropertyBar"
              class="picker-crafted-property-block"
            >
              <span class="picker-crafted-property-label">主属性</span>
              <div
                class="picker-stat-tabs picker-crafted-property-tabs"
                role="tablist"
                aria-label="自制装备主属性（力量 / 敏捷 / 智慧）"
              >
                <button
                  v-for="tab in CRAFTED_ARMOR_PROPERTY_TABS"
                  :key="tab.id"
                  type="button"
                  role="tab"
                  class="picker-stat-tab"
                  :class="{ active: craftedArmorStatPick === tab.id }"
                  :aria-selected="craftedArmorStatPick === tab.id"
                  @click="setCraftedArmorStatPick(tab.id)"
                >
                  {{ tab.label }}
                </button>
              </div>
            </div>

            <div
              v-if="showCraftedRingPropertyBar"
              class="picker-crafted-property-block"
            >
              <span class="picker-crafted-property-label">戒指类型</span>
              <div
                class="picker-stat-tabs picker-crafted-property-tabs"
                role="tablist"
                aria-label="自制戒指类型"
              >
                <button
                  v-for="tab in CRAFTED_RING_PROPERTY_TABS"
                  :key="tab.id"
                  type="button"
                  role="tab"
                  class="picker-stat-tab"
                  :class="{ active: craftedRingKindPick === tab.id }"
                  :aria-selected="craftedRingKindPick === tab.id"
                  @click="setCraftedRingKindPick(tab.id)"
                >
                  {{ tab.label }}
                </button>
              </div>
            </div>

            <div
              v-if="showCraftedWeaponCategoryBar"
              class="picker-crafted-property-block"
            >
              <span class="picker-crafted-property-label">武器类型</span>
              <div
                class="picker-stat-tabs picker-crafted-property-tabs picker-crafted-weapon-cat-tabs"
                role="tablist"
                aria-label="自制武器子类"
              >
                <button
                  v-for="tab in craftedWeaponCategoryTabsForCrafted"
                  :key="tab.id"
                  type="button"
                  role="tab"
                  class="picker-stat-tab"
                  :class="{ active: craftedWeaponCategoryPick === tab.id }"
                  :aria-selected="craftedWeaponCategoryPick === tab.id"
                  @click="setCraftedWeaponCategoryPick(tab.id)"
                >
                  {{ tab.label }}
                </button>
              </div>
            </div>

            <p
              v-if="showCraftedPropertyRequiredHint"
              class="picker-blocked-hint picker-blocked-hint--soft"
            >
              请先完成上方的属性或武器类型选择，再选择打造基底。
            </p>
          </template>

          <div
            v-if="craftedPropertyStepReady && craftedWhiteBaseRowsForActiveSlot.length > 0"
            class="picker-crafted-base-block"
          >
            <div class="picker-crafted-base-head">
              <span class="picker-crafted-base-label">打造基底</span>
              <button
                type="button"
                class="picker-crafted-base-collapse-toggle"
                :aria-expanded="!craftedBaseGridCollapsed"
                :disabled="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
                @click="craftedBaseGridCollapsed = !craftedBaseGridCollapsed"
              >
                {{ craftedBaseGridCollapsed ? '展开' : '收起' }}
              </button>
            </div>
            <template v-if="!craftedBaseGridCollapsed">
              <div class="picker-crafted-base-search-row">
                <input
                  v-model="craftedBaseSearchQuery"
                  type="search"
                  class="picker-search-input"
                  placeholder="按基底名称筛选…"
                  autocomplete="off"
                  spellcheck="false"
                  :disabled="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
                />
              </div>
              <div
                class="picker-crafted-base-grid"
                role="listbox"
                aria-label="打造基底列表"
              >
                <button
                  v-for="row in filteredCraftedWhiteBaseRows"
                  :key="`${row.affixCategorySlug}|${row.baseId}`"
                  type="button"
                  role="option"
                  class="picker-crafted-base-card"
                  :class="{
                    active:
                      craftedAffixCategorySlug === row.affixCategorySlug &&
                      craftedGearBaseId === row.baseId
                  }"
                  :aria-selected="
                    craftedAffixCategorySlug === row.affixCategorySlug &&
                    craftedGearBaseId === row.baseId
                  "
                  :title="row.name"
                  :disabled="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
                  @click="selectCraftedWhiteBase(row)"
                >
                  <span class="picker-crafted-base-card-icon-wrap">
                    <img
                      v-if="craftedBaseRowIconSrc(row)"
                      :src="craftedBaseRowIconSrc(row)"
                      class="picker-crafted-base-card-icon"
                      alt=""
                    />
                    <span v-else class="picker-crafted-base-card-icon picker-crafted-base-card-icon--empty" />
                  </span>
                  <span class="picker-crafted-base-card-name">{{ row.name }}</span>
                  <span
                    v-if="row.requiredLevel != null"
                    class="picker-crafted-base-card-lv"
                  >需求 {{ row.requiredLevel }}</span>
                  <span v-else class="picker-crafted-base-card-lv picker-crafted-base-card-lv--muted">—</span>
                </button>
                <p
                  v-if="filteredCraftedWhiteBaseRows.length === 0"
                  class="picker-empty picker-crafted-base-grid-empty"
                >
                  无匹配基底（请调整搜索）
                </p>
              </div>
            </template>
          </div>
          <p
            v-else-if="
              equipmentKind === 'crafted' &&
              craftedPropertyStepReady &&
              !craftedSlotHasAnyCraftedCategory &&
              !(activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded)
            "
            class="picker-empty picker-empty--inline"
          >
            当前部位暂无自制词缀数据（请检查 <code>craftedAffixes</code> 是否已同步）。
          </p>
          <p
            v-else-if="
              equipmentKind === 'crafted' &&
              craftedPropertyStepReady &&
              craftedSlotHasAnyCraftedCategory &&
              craftedWhiteBaseRowsForActiveSlot.length === 0 &&
              !(activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded)
            "
            class="picker-empty picker-empty--inline"
          >
            当前筛选下暂无可用基底（请调整属性 / 类型或同步 <code>craftedGearBases</code>）。
          </p>

          <p
            v-if="
              equipmentKind === 'crafted' &&
              craftedPropertyStepReady &&
              craftedWhiteBaseRowsForActiveSlot.length > 1 &&
              (!craftedAffixCategorySlug || !craftedGearBaseId) &&
              !(activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded)
            "
            class="picker-blocked-hint picker-blocked-hint--soft"
          >
            请先在列表中选择一件打造基底，再使用词缀类型、T 阶与词缀列表。
          </p>

          <template
            v-if="craftedAffixPickerUnlocked"
          >
            <div
              v-if="craftedAffixTypeTabs.length > 1"
              class="picker-stat-tabs picker-crafted-type-tabs"
              role="tablist"
              aria-label="词缀类型（含梦语后的高塔中阶 / 高阶）"
            >
              <button
                v-for="tab in craftedAffixTypeTabs"
                :key="tab.id"
                type="button"
                role="tab"
                class="picker-stat-tab picker-crafted-type-tab"
                :class="{ active: craftedAffixTypeFilter === tab.id }"
                :aria-selected="craftedAffixTypeFilter === tab.id"
                @click="craftedAffixTypeFilter = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>

            <!-- <p v-if="showTowerSequenceCraftedBlock" class="picker-hint picker-hint--tower-inline">
              <span class="picker-tower-inline-label">高塔序列</span>
              与基础 / 梦语 / 六槽独立，每件武器至多一条；点上方「中阶序列 / 高阶序列」查看词条。数据见
              <a
                class="picker-hint-link"
                href="https://tlidb.com/cn/TOWER_Sequence"
                target="_blank"
                rel="noopener noreferrer"
              >TLIDB 高塔序列</a>，同步 <code>npm run sync:tower-sequence-affixes</code>。
            </p> -->

            <div
              v-if="craftedTierTabs.length > 1 && !isCraftedAffixFilterTowerSequence"
              class="picker-stat-tabs picker-crafted-tier-tabs"
              role="tablist"
              aria-label="T 阶筛选"
            >
              <button
                v-for="tab in craftedTierTabs"
                :key="String(tab.id)"
                type="button"
                role="tab"
                class="picker-stat-tab"
                :class="{ active: craftedTierFilter === tab.id }"
                :aria-selected="craftedTierFilter === tab.id"
                @click="craftedTierFilter = tab.id"
              >
                {{ tab.label }}
              </button>
            </div>

            <p v-if="craftedAffixSlotsSummary" class="picker-crafted-slots-diag">{{ craftedAffixSlotsSummary }}</p>
            <p
              v-if="craftedAffixRuleHint"
              class="picker-crafted-rule-hint"
              role="alert"
            >
              <span class="picker-crafted-rule-hint-icon" aria-hidden="true">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  viewBox="0 0 24 24"
                  width="18"
                  height="18"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="2"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                >
                  <path
                    d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
              </span>
              <span class="picker-crafted-rule-hint-text">{{ craftedAffixRuleHint }}</span>
            </p>

            <div class="picker-search-row">
              <input
                v-model="pickerQuery"
                type="search"
                class="picker-search-input"
                placeholder="按词缀文案筛选…"
                autocomplete="off"
                spellcheck="false"
              />
            </div>

            <div class="picker-list">
              <template v-if="isCraftedAffixFilterTowerSequence">
                <button
                  v-for="row in filteredTowerSequenceRowsForPicker"
                  :key="'tower-row-' + row.modifierId"
                  type="button"
                  class="picker-item picker-item--crafted"
                  :class="{ active: towerSequenceRowIsEquipped(row) }"
                  :disabled="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
                  @click="equipTowerSequenceModifier(row)"
                >
                  <span class="picker-item-body">
                    <span class="picker-crafted-effect">{{ row.effectPlain }}</span>
                    <span class="picker-crafted-meta">
                      <span class="picker-crafted-atype">{{ row.affixType }}</span>
                      <span v-if="row.chipPattern" class="picker-crafted-w">芯片 {{ row.chipPattern }}</span>
                    </span>
                  </span>
                </button>
                <p v-if="filteredTowerSequenceRowsForPicker.length === 0" class="picker-empty">
                  无匹配高塔序列（可调整搜索或同步 <code>sync:tower-sequence-affixes</code>）
                </p>
              </template>
              <template v-else>
                <button
                  v-for="row in filteredCraftedModifierRows"
                  :key="`${row.sourceSlug}-${row.modifierId}`"
                  type="button"
                  class="picker-item picker-item--crafted"
                  :class="{ active: craftedModifierRowIsEquipped(row) }"
                  :disabled="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded"
                  @click="equipCraftedModifier(row)"
                >
                  <span class="picker-item-body">
                    <span class="picker-crafted-effect">{{ row.effectPlain }}</span>
                    <span class="picker-crafted-meta">
                      <span v-if="row.tier != null" class="picker-crafted-tier">{{ craftedTierLabel(row.tier) }}</span>
                      <span class="picker-crafted-atype">{{ craftedAffixTypeDisplay(row.affixType) }}</span>
                      <span v-if="row.itemLevel != null" class="picker-crafted-ilvl">ilvl {{ row.itemLevel }}</span>
                      <span v-if="row.weight != null" class="picker-crafted-w">权重 {{ row.weight }}</span>
                    </span>
                  </span>
                </button>
                <p v-if="filteredCraftedModifierRows.length === 0" class="picker-empty">
                  无匹配词缀（请调整筛选或同步 <code>sync:crafted-affixes</code>）
                </p>
              </template>
            </div>
          </template>
        </template>

        <template v-else>
          <h2 class="panel-title">选择 · {{ activeSlot.label }}</h2>
          <p class="picker-hint">
            列表来自 TLIDB 暗金（传奇）装备数据，已按当前部位筛选<span v-if="showArmorStatFilter">；头部 / 上衣 / 手套 / 鞋子可按主属性（力量、敏捷、智慧）进一步分类</span><span v-if="showRingKindFilter">；戒指位可分为「戒指」与「灵戒」</span><span v-if="showWeaponTypeFilter">；主武器 / 副武器可按武器类型（及副手的盾牌类型）筛选</span>。本部位共 {{ pickerOptionsForSlot.length }} 件<span v-if="pickerQuery.trim()">，名称匹配 {{ filteredPickerOptions.length }} 件</span>。
          </p>
          <p v-if="activeSlot.id === 'weapon_off' && equippedMainIsTwoHanded" class="picker-blocked-hint">
            当前主手为双手武器，无法装备副武器；请先更换主手或卸下双手武器。
          </p>

          <div
            v-if="showArmorStatFilter"
            class="picker-stat-tabs"
            role="tablist"
            aria-label="主属性筛选"
          >
            <button
              v-for="tab in ARMOR_STAT_TABS"
              :key="tab.id"
              type="button"
              role="tab"
              class="picker-stat-tab"
              :class="{ active: armorStatFilter === tab.id }"
              :aria-selected="armorStatFilter === tab.id"
              @click="armorStatFilter = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div
            v-if="showRingKindFilter"
            class="picker-stat-tabs"
            role="tablist"
            aria-label="戒指类型筛选"
          >
            <button
              v-for="tab in RING_KIND_TABS"
              :key="tab.id"
              type="button"
              role="tab"
              class="picker-stat-tab"
              :class="{ active: ringKindFilter === tab.id }"
              :aria-selected="ringKindFilter === tab.id"
              @click="ringKindFilter = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div
            v-if="showWeaponTypeFilter"
            class="picker-stat-tabs picker-weapon-type-tabs"
            role="tablist"
            aria-label="武器类型筛选"
          >
            <button
              v-for="tab in weaponTypeTabsForActiveSlot"
              :key="tab.id"
              type="button"
              role="tab"
              class="picker-stat-tab picker-weapon-type-tab"
              :class="{ active: weaponTypeFilter === tab.id }"
              :aria-selected="weaponTypeFilter === tab.id"
              @click="weaponTypeFilter = tab.id"
            >
              {{ tab.label }}
            </button>
          </div>

          <div class="picker-search-row">
            <input
              v-model="pickerQuery"
              type="search"
              class="picker-search-input"
              placeholder="按名称筛选…"
              autocomplete="off"
              spellcheck="false"
            />
          </div>

          <div class="picker-list">
            <button
              v-for="opt in filteredPickerOptions"
              :key="opt.id"
              type="button"
              class="picker-item picker-item--row"
              :class="{ active: currentEquipped?.id === opt.id }"
              @click="equipCurrent(opt)"
            >
              <img v-if="opt.iconUrl" :src="opt.iconUrl" class="picker-item-icon" alt="" />
              <span class="picker-item-body">
                <span class="picker-item-name-row">
                  <span class="picker-item-name">{{ opt.name }}</span>
                  <span
                    v-if="opt.statTag"
                    class="picker-item-stat-tag"
                    :data-stat="opt.statTag"
                  >{{ opt.statTag }}</span>
                  <span
                    v-if="opt.ringKindTag"
                    class="picker-item-ring-tag"
                    :data-kind="opt.ringKindTag"
                  >{{ opt.ringKindTag }}</span>
                  <span
                    v-if="opt.weaponTypeTag"
                    class="picker-item-weapon-tag"
                  >{{ opt.weaponTypeTag }}</span>
                </span>
                <span v-if="opt.requiredLevel != null" class="picker-item-meta">需求等级 {{ opt.requiredLevel }}</span>
              </span>
            </button>
            <p v-if="filteredPickerOptions.length === 0" class="picker-empty">
              无匹配装备（或该部位暂无暗金数据）
            </p>
          </div>
        </template>
      </section>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { useBuildStore } from '@/stores/build'
import legendaryGearJson from '@/data/equipment/legendaryGear.json'
import towerSequenceAffixesJson from '@/data/equipment/towerSequenceAffixes.json'
import EffectLineRollPicker from '@/components/equipment/EffectLineRollPicker.vue'
import { parseEffectLineRolls } from '@/utils/effectLineRolls'
import { buildCraftedDisplayLinesAndRemoveMeta } from '@/utils/weaponPhysicalFromEquipment'
import { resolveCraftedGearBaseIconUrl } from '@/utils/craftedGearBaseIcon'
import { resolveLegendaryGearIconUrl } from '@/utils/legendaryGearIcon'

type CraftedModifier = {
  modifierId: string
  tier: number | null
  itemLevel: number | null
  weight: number | null
  affixType: string
  source: string
  effectPlain: string
  valueSpans: string[]
}

type CraftedAffixFile = {
  kind?: string
  slug: string
  label: string
  modifiers?: CraftedModifier[]
}

type CraftedModifierRow = CraftedModifier & { sourceSlug: string }

type TowerSequenceModifierRow = CraftedModifier & {
  categorySlug: string
  chipPattern?: string | null
  sourceSlug: string
  towerSequence: true
}

type CraftedTierFilterId = 'all' | 't0plus' | 't0' | 't1' | 't2'

type TowerSequenceAffixJsonFile = {
  kind?: string
  modifiers?: Array<
    CraftedModifier & { categorySlug: string; chipPattern?: string | null }
  >
}

/** 右侧「底子装备」列表行：选定后决定词缀 JSON 子类 + 展示用基底信息 */
type CraftedWhiteBasePickerRow = {
  affixCategorySlug: string
  categoryDisplayLabel: string
  baseId: string
  name: string
  iconUrl?: string
  /** 同步脚本保留的 TLIDB CDN，供未下载图标时回退 */
  cdnIconUrl?: string
  requiredLevel?: number | null
  slotKind?: string
  baseEffectLines?: string[]
}

function craftedBaseRowIconSrc(row: CraftedWhiteBasePickerRow): string {
  if (row.baseId === '__category_only__') return ''
  return resolveCraftedGearBaseIconUrl({
    id: row.baseId,
    iconUrl: row.iconUrl,
    cdnIconUrl: row.cdnIconUrl
  })
}

const craftedAffixGlob = import.meta.glob<{ default: CraftedAffixFile }>(
  '@/data/equipment/craftedAffixes/*.json',
  { eager: true }
)

const craftedBySlug = new Map<string, CraftedAffixFile>()
for (const path of Object.keys(craftedAffixGlob)) {
  if (path.includes('index.json')) continue
  const data = craftedAffixGlob[path]?.default
  if (data?.slug && data.kind !== 'craftedAffixIndex') {
    craftedBySlug.set(data.slug, data)
  }
}

const TOWER_SEQUENCE_MODIFIER_ROWS: TowerSequenceModifierRow[] = (
  (towerSequenceAffixesJson as TowerSequenceAffixJsonFile).modifiers ?? []
).map(m => ({
  ...m,
  sourceSlug: m.categorySlug,
  towerSequence: true as const
}))

type CraftedGearBaseItem = {
  id: string
  name: string
  iconUrl?: string
  cdnIconUrl?: string
  iconAlt?: string
  requiredLevel?: number | null
  slotKind?: string
  baseEffectLines?: string[]
}

type CraftedGearBasesFile = {
  kind?: string
  categorySlug: string
  categoryLabel?: string
  bases?: CraftedGearBaseItem[]
}

const craftedGearBasesGlob = import.meta.glob<{ default: CraftedGearBasesFile }>(
  '@/data/equipment/craftedGearBases/*.json',
  { eager: true }
)

const craftedGearBasesBySlug = new Map<string, CraftedGearBasesFile>()
for (const path of Object.keys(craftedGearBasesGlob)) {
  if (path.includes('index.json')) continue
  const data = craftedGearBasesGlob[path]?.default
  if (data?.categorySlug && data.kind !== 'craftedGearBasesIndex') {
    craftedGearBasesBySlug.set(data.categorySlug, data)
  }
}

type LegendCategoryRef = { slug: string; label: string }
type LegendaryGearItem = {
  id: string
  name: string
  /** 展示用图标：本地化后为 /assets/equipment/legendary/... */
  iconUrl?: string
  /** 原始 CDN 地址，供同步脚本重新下载图标 */
  cdnIconUrl?: string
  localIconUrl?: string
  requiredLevel?: number
  categories: LegendCategoryRef[]
  /** 详情页解析的词条行（基础属性 + 传奇效果 + 风味描述等） */
  effectLines?: string[]
}

/** 已选中的自制打造词缀（占用 3 前缀 + 3 后缀 槽位之一） */
type CraftedEquippedAffix = {
  modifierId: string
  effectPlain: string
  affixType: string
  sourceSlug: string
  tier?: number | null
  /** 来自 TLIDB 高塔序列页，与六槽 / 基础 / 美梦独立 */
  towerSequence?: boolean
  chipPattern?: string | null
}

type EquippedItem = {
  id: string
  name: string
  iconUrl?: string
  requiredLevel?: number
  kind?: 'legendary' | 'crafted'
  /** 自制：已选词缀列表（至多 3 前缀 + 3 后缀；至臻、进阶各至多 2 条） */
  craftedAffixes?: CraftedEquippedAffix[]
  /** 自制：基础词缀（至多 2 条，展示在已选效果最前） */
  craftedBasicAffixes?: CraftedEquippedAffix[]
  /** 自制：美梦词缀（JSON 字段为「美梦词缀」，界面称梦语；至多 1 条） */
  craftedDreamAffixes?: CraftedEquippedAffix[]
  /** 自制主副手武器 / 盾牌：高塔序列（中阶或高阶；至多 1 条，见 TLIDB 高塔序列） */
  craftedTowerSequenceAffixes?: CraftedEquippedAffix[]
  /** 自制武器格：来源 TLIDB 子类 slug，用于双手武器判定 */
  craftedWeaponCategorySlug?: string
  /** 自制：词缀池所属子类（与 craftedAffixes 文件名一致） */
  craftedAffixCategorySlug?: string
  /** 自制：TLIDB Item 基底 id（href） */
  craftedGearBaseId?: string
  /** 自制：基底中文名 */
  craftedGearBaseName?: string
  /** 自制：基底自带词条（物理/暴击值/攻速等） */
  craftedBaseEffectLines?: string[]
}

/** 列表行：护甲四格可带主属性标签；戒指位可带戒指/灵戒标签 */
type ArmorStatLabel = '力量' | '敏捷' | '智慧'
type RingKindLabel = '戒指' | '灵戒'
type PickerEquipRow = EquippedItem & {
  statTag?: ArmorStatLabel
  ringKindTag?: RingKindLabel
  weaponTypeTag?: string
}

type ArmorStatFilter = 'all' | 'str' | 'dex' | 'int'

const ARMOR_STAT_TABS: { id: ArmorStatFilter; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'str', label: '力量' },
  { id: 'dex', label: '敏捷' },
  { id: 'int', label: '智慧' }
]

/** 自制护甲四格：第一步必选主属性 */
const CRAFTED_ARMOR_PROPERTY_TABS: { id: 'str' | 'dex' | 'int'; label: string }[] = [
  { id: 'str', label: '力量' },
  { id: 'dex', label: '敏捷' },
  { id: 'int', label: '智慧' }
]

/** 自制戒指位：第一步必选戒指 / 灵戒 */
const CRAFTED_RING_PROPERTY_TABS: { id: 'ring' | 'spirit_ring'; label: string }[] = [
  { id: 'ring', label: '戒指' },
  { id: 'spirit_ring', label: '灵戒' }
]

/**
 * 自制「词缀类型」筛选项：基础、梦语（美梦）、初阶/进阶/至臻 × 前缀/后缀（与 JSON 中 affixType 一致）。
 * 其它类型（如侵蚀基底、传奇专属等）仅在选「全部类型」时出现。
 */
const CRAFTED_STANDARD_AFFIX_TYPES: { typeId: string; label: string }[] = [
  { typeId: '基础词缀', label: '基础词缀' },
  { typeId: '美梦词缀', label: '梦语词缀' },
  { typeId: '初阶前缀', label: '初阶前缀' },
  { typeId: '初阶后缀', label: '初阶后缀' },
  { typeId: '进阶前缀', label: '进阶前缀' },
  { typeId: '进阶后缀', label: '进阶后缀' },
  { typeId: '至臻前缀', label: '至臻前缀' },
  { typeId: '至臻后缀', label: '至臻后缀' }
]

/** TLIDB 英文页「类型」列 → 中文 affixType（与 sync_crafted_gear_affixes.py 对齐） */
const CRAFTED_AFFIX_TYPE_EN_TO_ZH: Record<string, string> = {
  'base affix': '基础词缀',
  'sweet dream affix': '美梦词缀',
  'corrosion base': '侵蚀基底',
  'basic pre-fix': '初阶前缀',
  'advanced pre-fix': '进阶前缀',
  'ultimate pre-fix': '至臻前缀',
  'basic suffix': '初阶后缀',
  'advanced suffix': '进阶后缀',
  'ultimate suffix': '至臻后缀',
  'basic prefix': '初阶前缀',
  'advanced prefix': '进阶前缀',
  'ultimate prefix': '至臻前缀'
}

const CRAFTED_STANDARD_TYPE_IDS = new Set(CRAFTED_STANDARD_AFFIX_TYPES.map(x => x.typeId))

function normalizeCraftedDataAffixType(raw: string): string {
  const t = raw.trim()
  if (CRAFTED_STANDARD_TYPE_IDS.has(t)) return t
  const zh = CRAFTED_AFFIX_TYPE_EN_TO_ZH[t.toLowerCase()]
  return zh ?? t
}

/** 基础词缀额外槽位上限（与六条前后缀独立） */
const CRAFTED_BASIC_AFFIX_MAX = 2
/** 美梦（梦语）词缀上限 */
const CRAFTED_DREAM_AFFIX_MAX = 1
/** 高塔序列：每件武器 / 盾牌至多一条（中阶或高阶） */
const CRAFTED_TOWER_SEQUENCE_AFFIX_MAX = 1

function craftedAffixTypeDisplay(affixType: string): string {
  const hit = CRAFTED_STANDARD_AFFIX_TYPES.find(x => x.typeId === affixType)
  return hit?.label ?? affixType
}

function craftedTierLabel(tier: number | null | undefined): string {
  if (tier == null) return ''
  if (tier < 0) return 'T0+'
  if (tier === 0) return 'T0'
  if (tier === 1) return 'T1'
  if (tier === 2) return 'T2'
  return `T${tier}`
}

/** 占用「3 前缀 + 3 后缀」打造槽位的词缀类型（与 JSON affixType 一致） */
const CRAFTED_PREFIX_SLOT_TYPES = new Set(['初阶前缀', '进阶前缀', '至臻前缀'])
const CRAFTED_SUFFIX_SLOT_TYPES = new Set(['初阶后缀', '进阶后缀', '至臻后缀'])

function craftedAffixSlotKind(affixType: string): 'prefix' | 'suffix' | null {
  if (CRAFTED_PREFIX_SLOT_TYPES.has(affixType)) return 'prefix'
  if (CRAFTED_SUFFIX_SLOT_TYPES.has(affixType)) return 'suffix'
  return null
}

function craftedAffixIsZhen(affixType: string): boolean {
  return affixType.includes('至臻')
}

function craftedAffixIsJin(affixType: string): boolean {
  return affixType.includes('进阶')
}

function craftedEquipSlotId(slotIndex: number): string {
  return `crafted-slot-${slotIndex}`
}

function buildCraftedEquipItemName(baseName: string | undefined, affixCount: number): string {
  const b = baseName?.trim()
  if (b) return `${b}（${affixCount}/6）`
  return `自制（${affixCount}/6）`
}

/** 返回 null 表示可加入；否则为错误说明（仅六槽前后缀） */
function validateCraftedAffixAdd(
  existing: CraftedEquippedAffix[],
  row: { affixType: string; modifierId: string }
): string | null {
  const kind = craftedAffixSlotKind(row.affixType)
  if (!kind) {
    return '仅「基础词缀」「梦语词缀（美梦）」与初阶/进阶/至臻的前缀或后缀可点选加入；侵蚀基底等其它类型请仅作参考。'
  }
  if (existing.some(a => a.modifierId === row.modifierId)) {
    return '该词缀已在列表中，请使用左侧词条旁的 × 移除'
  }

  const prefixN = existing.filter(a => craftedAffixSlotKind(a.affixType) === 'prefix').length
  const suffixN = existing.filter(a => craftedAffixSlotKind(a.affixType) === 'suffix').length
  const zhenN = existing.filter(a => craftedAffixIsZhen(a.affixType)).length
  const jinN = existing.filter(a => craftedAffixIsJin(a.affixType)).length

  if (kind === 'prefix' && prefixN >= 3) return '前缀已满（最多 3 条）'
  if (kind === 'suffix' && suffixN >= 3) return '后缀已满（最多 3 条）'
  if (craftedAffixIsZhen(row.affixType) && zhenN >= 2) return '至臻词缀至多 2 条'
  if (craftedAffixIsJin(row.affixType) && jinN >= 2) return '进阶词缀至多 2 条'
  return null
}

function validateBasicAffixAdd(
  existing: CraftedEquippedAffix[],
  row: { modifierId: string }
): string | null {
  if (existing.some(a => a.modifierId === row.modifierId)) {
    return '该词缀已在列表中，请使用左侧词条旁的 × 移除'
  }
  if (existing.length >= CRAFTED_BASIC_AFFIX_MAX) return `基础词缀至多 ${CRAFTED_BASIC_AFFIX_MAX} 条`
  return null
}

function validateDreamAffixAdd(
  existing: CraftedEquippedAffix[],
  row: { modifierId: string }
): string | null {
  if (existing.some(a => a.modifierId === row.modifierId)) {
    return '该词缀已在列表中，请使用左侧词条旁的 × 移除'
  }
  if (existing.length >= CRAFTED_DREAM_AFFIX_MAX) return `梦语词缀至多 ${CRAFTED_DREAM_AFFIX_MAX} 条`
  return null
}

function validateTowerSequenceAffixAdd(
  existing: CraftedEquippedAffix[],
  row: { modifierId: string }
): string | null {
  if (existing.some(a => a.modifierId === row.modifierId)) {
    return '该序列已在列表中，请使用左侧词条旁的 × 移除'
  }
  if (existing.length >= CRAFTED_TOWER_SEQUENCE_AFFIX_MAX) {
    return `高塔序列至多 ${CRAFTED_TOWER_SEQUENCE_AFFIX_MAX} 条，请先移除当前序列再选择其它词条`
  }
  return null
}

/** 词缀全部卸空则返回 null（保留仅基底时仍保留装备条目） */
function craftedEntryAfterRemovingFrom(
  cur: EquippedItem,
  from: 'craft' | 'basic' | 'dream' | 'tower',
  modifierId: string
): EquippedItem | null {
  const nextCraft =
    from === 'craft'
      ? (cur.craftedAffixes ?? []).filter(a => a.modifierId !== modifierId)
      : [...(cur.craftedAffixes ?? [])]
  const nextBasic =
    from === 'basic'
      ? (cur.craftedBasicAffixes ?? []).filter(a => a.modifierId !== modifierId)
      : [...(cur.craftedBasicAffixes ?? [])]
  const nextDream =
    from === 'dream'
      ? (cur.craftedDreamAffixes ?? []).filter(a => a.modifierId !== modifierId)
      : [...(cur.craftedDreamAffixes ?? [])]
  const nextTower =
    from === 'tower'
      ? (cur.craftedTowerSequenceAffixes ?? []).filter(a => a.modifierId !== modifierId)
      : [...(cur.craftedTowerSequenceAffixes ?? [])]
  const total = nextCraft.length + nextBasic.length + nextDream.length + nextTower.length
  if (total === 0) {
    if (
      cur.kind === 'crafted' &&
      cur.craftedGearBaseId != null &&
      cur.craftedAffixCategorySlug != null
    ) {
      return {
        ...cur,
        craftedAffixes: undefined,
        craftedBasicAffixes: undefined,
        craftedDreamAffixes: undefined,
        craftedTowerSequenceAffixes: undefined,
        name: buildCraftedEquipItemName(cur.craftedGearBaseName, 0)
      }
    }
    return null
  }
  return {
    ...cur,
    craftedAffixes: nextCraft.length ? nextCraft : undefined,
    craftedBasicAffixes: nextBasic.length ? nextBasic : undefined,
    craftedDreamAffixes: nextDream.length ? nextDream : undefined,
    craftedTowerSequenceAffixes: nextTower.length ? nextTower : undefined,
    name: buildCraftedEquipItemName(cur.craftedGearBaseName, nextCraft.length)
  }
}

type RingKindFilter = 'all' | 'ring' | 'spirit_ring'

const RING_KIND_TABS: { id: RingKindFilter; label: string }[] = [
  { id: 'all', label: '全部' },
  { id: 'ring', label: '戒指' },
  { id: 'spirit_ring', label: '灵戒' }
]

/** 与格子顺序一致：两列一行，共五行 */
const EQUIPMENT_SLOTS = [
  { id: 'helmet', label: '头部' },
  { id: 'chest', label: '上衣' },
  { id: 'necklace', label: '项链' },
  { id: 'gloves', label: '手套' },
  { id: 'belt', label: '腰带' },
  { id: 'boots', label: '鞋子' },
  { id: 'ring1', label: '戒指1' },
  { id: 'ring2', label: '戒指2' },
  { id: 'weapon_main', label: '主武器' },
  { id: 'weapon_off', label: '副武器' }
] as const

const WEAPON_MAIN_SLOT_INDEX = EQUIPMENT_SLOTS.findIndex(s => s.id === 'weapon_main')
const WEAPON_OFF_SLOT_INDEX = EQUIPMENT_SLOTS.findIndex(s => s.id === 'weapon_off')

type EquipmentSlotId = (typeof EQUIPMENT_SLOTS)[number]['id']

/** 头部、上衣、手套、鞋子：按 STR / DEX / INT 子类筛选 */
const ARMOR_STAT_FILTER_SLOT_IDS = new Set<EquipmentSlotId>(['helmet', 'chest', 'gloves', 'boots'])

/** 戒指 1 / 戒指 2：按 Ring / Spirit_Ring 子类筛选 */
const RING_KIND_FILTER_SLOT_IDS = new Set<EquipmentSlotId>(['ring1', 'ring2'])

/** 武器子类顺序（与筛选标签顺序一致） */
const WEAPON_CATEGORY_TAB_ORDER: readonly string[] = [
  'Claw',
  'Dagger',
  'One-Handed_Sword',
  'One-Handed_Hammer',
  'One-Handed_Axe',
  'Wand',
  'Rod',
  'Scepter',
  'Cane',
  'Pistol',
  'Two-Handed_Sword',
  'Two-Handed_Hammer',
  'Two-Handed_Axe',
  'Tin_Staff',
  'Cudgel',
  'Bow',
  'Crossbow',
  'Musket',
  'Fire_Cannon'
]

/** 副手不可装备双手近战（与 TLIDB 分类一致） */
const TWO_HANDED_WEAPON_SLUGS: ReadonlySet<string> = new Set([
  'Two-Handed_Sword',
  'Two-Handed_Hammer',
  'Two-Handed_Axe'
])

/** 副武器武器类型标签顺序（不含双手剑/锤/斧） */
const WEAPON_CATEGORY_TAB_ORDER_OFF_HAND = WEAPON_CATEGORY_TAB_ORDER.filter(
  s => !TWO_HANDED_WEAPON_SLUGS.has(s)
)

const SHIELD_CATEGORY_TAB_ORDER: readonly string[] = ['STR_Shield', 'DEX_Shield', 'INT_Shield']

/** TLIDB 传奇装备「武器」子类（不含盾牌）；主手仅显示这些 */
const LEGENDARY_WEAPON_SLUGS: ReadonlySet<string> = new Set(WEAPON_CATEGORY_TAB_ORDER)

const LEGENDARY_SHIELD_SLUGS: ReadonlySet<string> = new Set(SHIELD_CATEGORY_TAB_ORDER)

/** 武器 / 盾牌 slug → 中文标签（筛选与列表角标） */
const WEAPON_TYPE_ZH: Readonly<Record<string, string>> = {
  Claw: '爪',
  Dagger: '匕首',
  'One-Handed_Sword': '单手剑',
  'One-Handed_Hammer': '单手锤',
  'One-Handed_Axe': '单手斧',
  Wand: '魔杖',
  Rod: '法杖',
  Scepter: '权杖',
  Cane: '手杖',
  Pistol: '手枪',
  'Two-Handed_Sword': '双手剑',
  'Two-Handed_Hammer': '双手锤',
  'Two-Handed_Axe': '双手斧',
  Tin_Staff: '锡杖',
  Cudgel: '棍棒',
  Bow: '弓',
  Crossbow: '弩',
  Musket: '火枪',
  Fire_Cannon: '火炮',
  STR_Shield: '力量盾',
  DEX_Shield: '敏捷盾',
  INT_Shield: '智慧盾'
}

function itemIsTwoHandedWeapon(item: LegendaryGearItem): boolean {
  return item.categories?.some(c => TWO_HANDED_WEAPON_SLUGS.has(c.slug)) ?? false
}

function allowedLegendSlugsForSlot(slotId: EquipmentSlotId): ReadonlySet<string> {
  switch (slotId) {
    case 'helmet':
      return new Set(['STR_Helmet', 'DEX_Helmet', 'INT_Helmet'])
    case 'chest':
      return new Set(['STR_Chest_Armor', 'DEX_Chest_Armor', 'INT_Chest_Armor'])
    case 'necklace':
      return new Set(['Necklace'])
    case 'gloves':
      return new Set(['STR_Gloves', 'DEX_Gloves', 'INT_Gloves'])
    case 'belt':
      return new Set(['Belt'])
    case 'boots':
      return new Set(['STR_Boots', 'DEX_Boots', 'INT_Boots'])
    case 'ring1':
    case 'ring2':
      return new Set(['Ring', 'Spirit_Ring'])
    case 'weapon_main':
      return LEGENDARY_WEAPON_SLUGS
    case 'weapon_off':
      return new Set([...LEGENDARY_WEAPON_SLUGS, ...LEGENDARY_SHIELD_SLUGS])
  }
}

/** 自制：底子按钮展示名（与 TLIDB 子类 slug 对应） */
function craftedBaseOptionLabel(slotId: EquipmentSlotId, slug: string): string {
  const zh = WEAPON_TYPE_ZH[slug]
  if (zh) return zh
  if (slug === 'Necklace') return '项链'
  if (slug === 'Belt') return '腰带'
  if (slug === 'Ring') return '戒指'
  if (slug === 'Spirit_Ring') return '灵戒'
  const part =
    slotId === 'helmet'
      ? '头部'
      : slotId === 'chest'
        ? '胸甲'
        : slotId === 'gloves'
          ? '手套'
          : slotId === 'boots'
            ? '鞋子'
            : ''
  if (part && slug.startsWith('STR_')) return `力量${part}`
  if (part && slug.startsWith('DEX_')) return `敏捷${part}`
  if (part && slug.startsWith('INT_')) return `智慧${part}`
  return craftedBySlug.get(slug)?.label ?? slug
}

function armorStatLabelForItem(item: LegendaryGearItem, slotId: EquipmentSlotId): ArmorStatLabel | undefined {
  if (!ARMOR_STAT_FILTER_SLOT_IDS.has(slotId)) return undefined
  const allowed = allowedLegendSlugsForSlot(slotId)
  for (const c of item.categories ?? []) {
    if (!allowed.has(c.slug)) continue
    if (c.slug.startsWith('STR_')) return '力量'
    if (c.slug.startsWith('DEX_')) return '敏捷'
    if (c.slug.startsWith('INT_')) return '智慧'
  }
  return undefined
}

function itemMatchesArmorStatFilter(
  item: LegendaryGearItem,
  slotId: EquipmentSlotId,
  filter: ArmorStatFilter
): boolean {
  if (filter === 'all') return true
  const prefix = filter === 'str' ? 'STR_' : filter === 'dex' ? 'DEX_' : 'INT_'
  const allowed = allowedLegendSlugsForSlot(slotId)
  return item.categories?.some(c => allowed.has(c.slug) && c.slug.startsWith(prefix)) ?? false
}

function ringKindLabelForItem(item: LegendaryGearItem, slotId: EquipmentSlotId): RingKindLabel | undefined {
  if (!RING_KIND_FILTER_SLOT_IDS.has(slotId)) return undefined
  const allowed = allowedLegendSlugsForSlot(slotId)
  for (const c of item.categories ?? []) {
    if (!allowed.has(c.slug)) continue
    if (c.slug === 'Spirit_Ring') return '灵戒'
    if (c.slug === 'Ring') return '戒指'
  }
  return undefined
}

function itemMatchesRingKindFilter(item: LegendaryGearItem, filter: RingKindFilter): boolean {
  if (filter === 'all') return true
  const slugs = new Set((item.categories ?? []).map(c => c.slug))
  if (filter === 'ring') return slugs.has('Ring')
  return slugs.has('Spirit_Ring')
}

const WEAPON_FILTER_SLOT_IDS = new Set<EquipmentSlotId>(['weapon_main', 'weapon_off'])

function weaponTypeLabelForItem(item: LegendaryGearItem, slotId: EquipmentSlotId): string | undefined {
  if (!WEAPON_FILTER_SLOT_IDS.has(slotId)) return undefined
  const allowed = allowedLegendSlugsForSlot(slotId)
  const order =
    slotId === 'weapon_off'
      ? [...WEAPON_CATEGORY_TAB_ORDER_OFF_HAND, ...SHIELD_CATEGORY_TAB_ORDER]
      : [...WEAPON_CATEGORY_TAB_ORDER]
  for (const slug of order) {
    if (!allowed.has(slug)) continue
    if (item.categories?.some(c => c.slug === slug)) {
      return WEAPON_TYPE_ZH[slug] ?? slug
    }
  }
  return undefined
}

function itemMatchesWeaponTypeFilter(
  item: LegendaryGearItem,
  slotId: EquipmentSlotId,
  filterSlug: string
): boolean {
  if (filterSlug === 'all') return true
  const allowed = allowedLegendSlugsForSlot(slotId)
  if (!allowed.has(filterSlug)) return false
  return item.categories?.some(c => c.slug === filterSlug) ?? false
}

const allLegendaryItems = legendaryGearJson.items as LegendaryGearItem[]

type EquipmentKind = 'legendary' | 'crafted'

/** 未选择时锁定装备栏与筛选，仅「暗金 / 自制」可点 */
/** 默认暗金：避免左侧装备格因「未选类型」被 pointer-events 锁死而无法切换 */
const equipmentKind = ref<EquipmentKind | null>('legendary')
const equipmentUiUnlocked = computed(() => equipmentKind.value != null)

const selectedSlotIndex = ref(0)

/** 自制词缀列表：校验失败时的简短提示（如槽位已满、类型不占槽） */
const craftedAffixRuleHint = ref<string | null>(null)
const equipped = ref<(EquippedItem | null)[]>(
  Array.from({ length: EQUIPMENT_SLOTS.length }, () => null)
)
const pickerQuery = ref('')
const armorStatFilter = ref<ArmorStatFilter>('all')
const ringKindFilter = ref<RingKindFilter>('all')
/** 主武器 / 副武器：'all' 或 TLIDB 分类 slug */
const weaponTypeFilter = ref<string>('all')

/** 自制：词缀类型（基础词缀、初阶前缀等） */
const craftedAffixTypeFilter = ref<string>('all')
/** 打造基底网格：默认展开；从「全部类型」选到具体类型时自动收起，可手动展开/收起 */
const craftedBaseGridCollapsed = ref(false)
/** 自制打造 T 档：TLIDB 维度 T0+ / T0 / T1 / T2 */
const craftedTierFilter = ref<CraftedTierFilterId>('all')
/** 自制：词缀池子类 slug（与 craftedAffixes/*.json 对应） */
const craftedAffixCategorySlug = ref<string | null>(null)
/** 自制：打造基底 id（TLIDB Item 页 href，如 Brute's_Helm） */
const craftedGearBaseId = ref<string | null>(null)
/** 底子列表本地搜索（与词缀搜索 pickerQuery 分离） */
const craftedBaseSearchQuery = ref('')
/** 自制护甲：先选力量 / 敏捷 / 智慧 */
const craftedArmorStatPick = ref<'str' | 'dex' | 'int' | null>(null)
/** 自制戒指位：先选戒指 / 灵戒 */
const craftedRingKindPick = ref<'ring' | 'spirit_ring' | null>(null)
/** 自制主副手：先选武器类型 slug（如 One-Handed_Sword） */
const craftedWeaponCategoryPick = ref<string | null>(null)

const legendaryById = computed(() => {
  const m = new Map<string, LegendaryGearItem>()
  for (const it of allLegendaryItems) {
    m.set(it.id, it)
  }
  return m
})

const equippedMainIsTwoHanded = computed((): boolean => {
  const eq = equipped.value[WEAPON_MAIN_SLOT_INDEX]
  if (!eq) return false
  if (eq.kind === 'crafted') {
    const w = eq.craftedWeaponCategorySlug ?? eq.craftedAffixCategorySlug
    if (w) return TWO_HANDED_WEAPON_SLUGS.has(w)
  }
  const raw = legendaryById.value.get(eq.id)
  return raw ? itemIsTwoHandedWeapon(raw) : false
})

/** 自制词条行：供左侧 × 移除 */
type CraftedEffectLineRemoveMeta = {
  modifierId: string
  pool: 'craft' | 'basic' | 'dream' | 'tower'
}

type EquippedEffectBlock = {
  slotIndex: number
  itemId: string
  slotLabel: string
  itemName: string
  lines: string[]
  blockKind?: 'crafted' | 'legendary'
  /** 与 lines 下标一一对应，仅自制装备有值 */
  craftedLineRemoveMeta?: Array<CraftedEffectLineRemoveMeta | null>
}

const equippedEffectsBlocks = computed((): EquippedEffectBlock[] => {
  const byId = legendaryById.value
  const out: EquippedEffectBlock[] = []
  equipped.value.forEach((eq, index) => {
    if (!eq) return
    if (eq.kind === 'crafted') {
      const { lines, craftedLineRemoveMeta } = buildCraftedDisplayLinesAndRemoveMeta(
        eq as unknown as Record<string, unknown>
      )
      out.push({
        slotIndex: index,
        itemId: String(eq.id ?? '').trim(),
        slotLabel: EQUIPMENT_SLOTS[index]!.label,
        itemName: eq.name,
        lines,
        blockKind: 'crafted',
        craftedLineRemoveMeta
      })
      return
    }
    const raw = byId.get(eq.id)
    const lines = Array.isArray(raw?.effectLines)
      ? raw!.effectLines!.map(l => String(l).trim()).filter(Boolean)
      : []
    out.push({
      slotIndex: index,
      itemId: String(eq.id ?? '').trim(),
      slotLabel: EQUIPMENT_SLOTS[index]!.label,
      itemName: eq.name,
      lines,
      blockKind: 'legendary'
    })
  })
  return out
})

function isFlavorEffectLine(line: string): boolean {
  const t = line.trim()
  return t.startsWith('「') && t.endsWith('」')
}

/** 词条内数值区间下拉框的当前选项，key 形如 slot|itemId|lineIndex#pickIndex */
const effectRollSelections = ref<Record<string, string>>({})

function onEffectRollPick(key: string, value: string) {
  effectRollSelections.value = { ...effectRollSelections.value, [key]: value }
}

watch(
  equippedEffectsBlocks,
  blocks => {
    const valid = new Set<string>()
    for (const block of blocks) {
      block.lines.forEach((line, li) => {
        if (isFlavorEffectLine(line)) return
        const segs = parseEffectLineRolls(line)
        if (!segs) return
        let pi = 0
        for (const s of segs) {
          if (s.type === 'pick') {
            valid.add(`${block.slotIndex}|${block.itemId}|${li}#${pi}`)
            pi++
          }
        }
      })
    }
    if (valid.size === 0) return
    const next = { ...effectRollSelections.value }
    let changed = false
    for (const k of Object.keys(next)) {
      if (!valid.has(k)) {
        delete next[k]
        changed = true
      }
    }
    if (changed) effectRollSelections.value = next
  },
  { deep: true }
)

const activeSlot = computed(() => EQUIPMENT_SLOTS[selectedSlotIndex.value]!)

/** 当前部位是否存在任意可自制子类（与是否已选属性无关） */
const craftedSlotHasAnyCraftedCategory = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  const slotId = activeSlot.value.id
  let slugs = [...allowedLegendSlugsForSlot(slotId)].filter(s => craftedBySlug.has(s))
  if (slotId === 'weapon_off') {
    slugs = slugs.filter(s => !TWO_HANDED_WEAPON_SLUGS.has(s))
  }
  return slugs.length > 0
})

const showCraftedArmorPropertyBar = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  return ARMOR_STAT_FILTER_SLOT_IDS.has(activeSlot.value.id)
})

const showCraftedRingPropertyBar = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  return RING_KIND_FILTER_SLOT_IDS.has(activeSlot.value.id)
})

const craftedWeaponCategoryTabsForCrafted = computed((): { id: string; label: string }[] => {
  if (equipmentKind.value !== 'crafted') return []
  const slotId = activeSlot.value.id
  if (slotId !== 'weapon_main' && slotId !== 'weapon_off') return []
  let slugs = [...allowedLegendSlugsForSlot(slotId)].filter(s => craftedBySlug.has(s))
  if (slotId === 'weapon_off') {
    slugs = slugs.filter(s => !TWO_HANDED_WEAPON_SLUGS.has(s))
  }
  const order =
    slotId === 'weapon_off'
      ? [...WEAPON_CATEGORY_TAB_ORDER_OFF_HAND, ...SHIELD_CATEGORY_TAB_ORDER]
      : [...WEAPON_CATEGORY_TAB_ORDER]
  return order.filter(s => slugs.includes(s)).map(s => ({ id: s, label: WEAPON_TYPE_ZH[s] ?? s }))
})

const showCraftedWeaponCategoryBar = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  const id = activeSlot.value.id
  if (id !== 'weapon_main' && id !== 'weapon_off') return false
  return craftedWeaponCategoryTabsForCrafted.value.length > 0
})

/** 已完成「属性 / 戒指类型 / 武器类型」第一步；项链、腰带等无需第一步时为 true */
const craftedPropertyStepReady = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  const slotId = activeSlot.value.id
  if (ARMOR_STAT_FILTER_SLOT_IDS.has(slotId)) return craftedArmorStatPick.value != null
  if (RING_KIND_FILTER_SLOT_IDS.has(slotId)) return craftedRingKindPick.value != null
  if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    if (craftedWeaponCategoryTabsForCrafted.value.length === 0) return true
    return craftedWeaponCategoryPick.value != null
  }
  return true
})

const showCraftedPropertyRequiredHint = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  if (craftedPropertyStepReady.value) return false
  return (
    showCraftedArmorPropertyBar.value ||
    showCraftedRingPropertyBar.value ||
    showCraftedWeaponCategoryBar.value
  )
})

const craftedWhiteBaseRowsForActiveSlot = computed((): CraftedWhiteBasePickerRow[] => {
  if (equipmentKind.value !== 'crafted') return []
  const slotId = activeSlot.value.id
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return []

  let slugs = [...allowedLegendSlugsForSlot(slotId)].filter(s => craftedBySlug.has(s))
  if (slotId === 'weapon_off') {
    slugs = slugs.filter(s => !TWO_HANDED_WEAPON_SLUGS.has(s))
  }

  if (ARMOR_STAT_FILTER_SLOT_IDS.has(slotId)) {
    const p = craftedArmorStatPick.value
    if (!p) return []
    const prefix = p === 'str' ? 'STR_' : p === 'dex' ? 'DEX_' : 'INT_'
    slugs = slugs.filter(s => s.startsWith(prefix))
  } else if (RING_KIND_FILTER_SLOT_IDS.has(slotId)) {
    const rk = craftedRingKindPick.value
    if (!rk) return []
    slugs = slugs.filter(
      s => (rk === 'ring' && s === 'Ring') || (rk === 'spirit_ring' && s === 'Spirit_Ring')
    )
  } else if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    if (craftedWeaponCategoryTabsForCrafted.value.length === 0) {
      /* 无可用子类标签时不强制选类型 */
    } else {
      const wc = craftedWeaponCategoryPick.value
      if (!wc) return []
      slugs = slugs.filter(s => s === wc)
    }
  }

  const rows: CraftedWhiteBasePickerRow[] = []
  for (const slug of slugs) {
    const catLabel = craftedBaseOptionLabel(slotId, slug)
    const file = craftedGearBasesBySlug.get(slug)
    const bases = file?.bases
    if (Array.isArray(bases) && bases.length > 0) {
      for (const b of bases) {
        rows.push({
          affixCategorySlug: slug,
          categoryDisplayLabel: catLabel,
          baseId: b.id,
          name: b.name,
          iconUrl: b.iconUrl,
          cdnIconUrl: b.cdnIconUrl,
          requiredLevel: b.requiredLevel ?? undefined,
          slotKind: b.slotKind,
          baseEffectLines: Array.isArray(b.baseEffectLines)
            ? b.baseEffectLines.map(x => String(x).trim()).filter(Boolean)
            : undefined
        })
      }
    } else {
      rows.push({
        affixCategorySlug: slug,
        categoryDisplayLabel: catLabel,
        baseId: '__category_only__',
        name: `${catLabel}（未同步基底，仅选词缀池）`,
        iconUrl: undefined,
        requiredLevel: undefined
      })
    }
  }
  rows.sort((a, b) => {
    const la = a.requiredLevel ?? -1
    const lb = b.requiredLevel ?? -1
    if (la !== lb) return lb - la
    const c = a.categoryDisplayLabel.localeCompare(b.categoryDisplayLabel, 'zh-CN')
    if (c !== 0) return c
    return a.name.localeCompare(b.name, 'zh-CN')
  })
  return rows
})

const filteredCraftedWhiteBaseRows = computed((): CraftedWhiteBasePickerRow[] => {
  const q = craftedBaseSearchQuery.value.trim().toLowerCase()
  const list = craftedWhiteBaseRowsForActiveSlot.value
  if (!q) return list
  return list.filter(
    r =>
      r.name.toLowerCase().includes(q) ||
      r.categoryDisplayLabel.toLowerCase().includes(q) ||
      r.baseId.toLowerCase().includes(q)
  )
})

/** 可展示词缀类型 / T 阶 / 词缀列表 */
const craftedAffixPickerUnlocked = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  if (!craftedPropertyStepReady.value) return false
  return !!(craftedAffixCategorySlug.value && craftedGearBaseId.value)
})

const showArmorStatFilter = computed(() => ARMOR_STAT_FILTER_SLOT_IDS.has(activeSlot.value.id))
const showRingKindFilter = computed(() => RING_KIND_FILTER_SLOT_IDS.has(activeSlot.value.id))

const weaponTypeTabsForActiveSlot = computed((): { id: string; label: string }[] => {
  const id = activeSlot.value.id
  const slugs =
    id === 'weapon_off'
      ? [...WEAPON_CATEGORY_TAB_ORDER_OFF_HAND, ...SHIELD_CATEGORY_TAB_ORDER]
      : id === 'weapon_main'
        ? [...WEAPON_CATEGORY_TAB_ORDER]
        : []
  if (!slugs.length) return []
  return [
    { id: 'all', label: '全部' },
    ...slugs.map(s => ({ id: s, label: WEAPON_TYPE_ZH[s] ?? s }))
  ]
})

const showWeaponTypeFilter = computed(() => weaponTypeTabsForActiveSlot.value.length > 0)

const equippedCount = computed(() => equipped.value.filter(Boolean).length)

const currentEquipped = computed(() => equipped.value[selectedSlotIndex.value] ?? null)

const craftedAffixSlotsSummary = computed((): string | null => {
  const eq = currentEquipped.value
  if (eq?.kind !== 'crafted') return null
  const basicN = eq.craftedBasicAffixes?.length ?? 0
  const dreamN = eq.craftedDreamAffixes?.length ?? 0
  const towerN = eq.craftedTowerSequenceAffixes?.length ?? 0
  const list = eq.craftedAffixes ?? []
  const craftN = list.length
  if (basicN === 0 && dreamN === 0 && towerN === 0 && craftN === 0) return null
  const pn = list.filter(a => craftedAffixSlotKind(a.affixType) === 'prefix').length
  const sn = list.filter(a => craftedAffixSlotKind(a.affixType) === 'suffix').length
  const zn = list.filter(a => craftedAffixIsZhen(a.affixType)).length
  const jn = list.filter(a => craftedAffixIsJin(a.affixType)).length
  return `已选：基础 ${basicN}/${CRAFTED_BASIC_AFFIX_MAX}，梦语 ${dreamN}/${CRAFTED_DREAM_AFFIX_MAX}，高塔序列 ${towerN}/${CRAFTED_TOWER_SEQUENCE_AFFIX_MAX}；前缀 ${pn}/3，后缀 ${sn}/3；至臻 ${zn}/2，进阶 ${jn}/2`
})

function craftedModifierRowIsEquipped(row: CraftedModifierRow): boolean {
  const eq = equipped.value[selectedSlotIndex.value]
  if (eq?.kind !== 'crafted') return false
  const id = row.modifierId
  return !!(
    eq.craftedAffixes?.some(a => a.modifierId === id) ||
    eq.craftedBasicAffixes?.some(a => a.modifierId === id) ||
    eq.craftedDreamAffixes?.some(a => a.modifierId === id)
  )
}

const pickerOptionsForSlot = computed((): PickerEquipRow[] => {
  const slotId = activeSlot.value.id
  const allowed = allowedLegendSlugsForSlot(slotId)
  let rows = allLegendaryItems.filter(item => item.categories?.some(c => allowed.has(c.slug)))
  if (ARMOR_STAT_FILTER_SLOT_IDS.has(slotId)) {
    rows = rows.filter(item => itemMatchesArmorStatFilter(item, slotId, armorStatFilter.value))
  }
  if (RING_KIND_FILTER_SLOT_IDS.has(slotId)) {
    rows = rows.filter(item => itemMatchesRingKindFilter(item, ringKindFilter.value))
  }
  if (WEAPON_FILTER_SLOT_IDS.has(slotId)) {
    rows = rows.filter(item => itemMatchesWeaponTypeFilter(item, slotId, weaponTypeFilter.value))
  }
  if (slotId === 'weapon_off') {
    rows = rows.filter(item => !itemIsTwoHandedWeapon(item))
    if (equippedMainIsTwoHanded.value) {
      rows = []
    }
  }
  return rows
    .map(item => ({
      id: item.id,
      name: item.name,
      iconUrl: resolveLegendaryGearIconUrl(item),
      requiredLevel: item.requiredLevel,
      statTag: armorStatLabelForItem(item, slotId),
      ringKindTag: ringKindLabelForItem(item, slotId),
      weaponTypeTag: weaponTypeLabelForItem(item, slotId)
    }))
    .sort((a, b) => {
      const la = a.requiredLevel ?? 0
      const lb = b.requiredLevel ?? 0
      if (la !== lb) return la - lb
      return a.name.localeCompare(b.name, 'zh-CN')
    })
})

const filteredPickerOptions = computed((): PickerEquipRow[] => {
  const q = pickerQuery.value.trim().toLowerCase()
  const list = pickerOptionsForSlot.value
  if (!q) return list
  return list.filter(o => o.name.toLowerCase().includes(q))
})

const craftedModifierRowsForActiveSlot = computed((): CraftedModifierRow[] => {
  if (equipmentKind.value !== 'crafted') return []
  const slotId = activeSlot.value.id
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return []
  const slug = craftedAffixCategorySlug.value
  if (!slug) return []
  const file = craftedBySlug.get(slug)
  const mods = file?.modifiers
  if (!mods?.length) return []
  return mods.map(m => ({
    ...m,
    affixType: normalizeCraftedDataAffixType(m.affixType),
    sourceSlug: slug
  }))
})

const craftedAffixTypeTabs = computed((): { id: string; label: string }[] => {
  const present = new Set(
    craftedModifierRowsForActiveSlot.value.map(r => r.affixType).filter(Boolean)
  )
  const tabs: { id: string; label: string }[] = [{ id: 'all', label: '全部类型' }]
  const slug = craftedAffixCategorySlug.value
  const slotId = activeSlot.value.id
  const towerAfterDream =
    equipmentKind.value === 'crafted' &&
    craftedAffixPickerUnlocked.value &&
    (slotId === 'weapon_main' || slotId === 'weapon_off') &&
    !(slotId === 'weapon_off' && equippedMainIsTwoHanded.value) &&
    !!slug &&
    LEGENDARY_WEAPON_SLUGS.has(slug)

  for (const { typeId, label } of CRAFTED_STANDARD_AFFIX_TYPES) {
    if (present.has(typeId)) {
      tabs.push({ id: typeId, label })
    }
    if (typeId === '美梦词缀' && towerAfterDream) {
      const towerTypes = new Set(
        TOWER_SEQUENCE_MODIFIER_ROWS.filter(r => r.sourceSlug === slug).map(r => r.affixType)
      )
      if (towerTypes.has('中阶序列')) tabs.push({ id: '中阶序列', label: '中阶序列' })
      if (towerTypes.has('高阶序列')) tabs.push({ id: '高阶序列', label: '高阶序列' })
    }
  }
  return tabs
})

const craftedTierTabs = computed((): { id: CraftedTierFilterId; label: string }[] => {
  // 与 TLIDB 打造页维度对齐：始终展示 T0+ / T0 / T1 / T2 四档
  return [
    { id: 'all', label: '全部 T 档' },
    { id: 't0plus', label: 'T0+' },
    { id: 't0', label: 'T0' },
    { id: 't1', label: 'T1' },
    { id: 't2', label: 'T2' }
  ]
})

const isCraftedAffixFilterTowerSequence = computed(
  () =>
    craftedAffixTypeFilter.value === '中阶序列' || craftedAffixTypeFilter.value === '高阶序列'
)

const filteredCraftedModifierRows = computed((): CraftedModifierRow[] => {
  if (isCraftedAffixFilterTowerSequence.value) return []
  let list = [...craftedModifierRowsForActiveSlot.value]
  if (craftedAffixTypeFilter.value !== 'all') {
    list = list.filter(r => r.affixType === craftedAffixTypeFilter.value)
  }
  if (craftedTierFilter.value !== 'all') {
    list = list.filter(r => {
      if (r.tier == null) return false
      if (craftedTierFilter.value === 't0plus') return r.tier < 0
      if (craftedTierFilter.value === 't0') return r.tier === 0
      if (craftedTierFilter.value === 't1') return r.tier === 1
      if (craftedTierFilter.value === 't2') return r.tier === 2
      return true
    })
  }
  const q = pickerQuery.value.trim().toLowerCase()
  if (q) list = list.filter(r => r.effectPlain.toLowerCase().includes(q))
  return list.sort((a, b) => {
    const ta = a.tier ?? 999
    const tb = b.tier ?? 999
    if (ta !== tb) return ta - tb
    const sa = a.sourceSlug.localeCompare(b.sourceSlug)
    if (sa !== 0) return sa
    return a.effectPlain.localeCompare(b.effectPlain, 'zh-CN')
  })
})

const filteredTowerSequenceRowsForPicker = computed((): TowerSequenceModifierRow[] => {
  if (!isCraftedAffixFilterTowerSequence.value) return []
  if (equipmentKind.value !== 'crafted') return []
  const slotId = activeSlot.value.id
  if (slotId !== 'weapon_main' && slotId !== 'weapon_off') return []
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return []
  const slug = craftedAffixCategorySlug.value
  if (!slug || !LEGENDARY_WEAPON_SLUGS.has(slug)) return []
  const aff = craftedAffixTypeFilter.value
  let rows = TOWER_SEQUENCE_MODIFIER_ROWS.filter(
    r => r.sourceSlug === slug && r.affixType === aff
  )
  const q = pickerQuery.value.trim().toLowerCase()
  if (q) rows = rows.filter(r => r.effectPlain.toLowerCase().includes(q))
  return rows.sort((a, b) => a.effectPlain.localeCompare(b.effectPlain, 'zh-CN'))
})

/** 仅当前子类为武器（非盾牌）时展示高塔序列的中阶 / 高阶筛选与列表 */
const showTowerSequenceCraftedBlock = computed((): boolean => {
  if (equipmentKind.value !== 'crafted') return false
  if (!craftedAffixPickerUnlocked.value) return false
  const slotId = activeSlot.value.id
  if (slotId !== 'weapon_main' && slotId !== 'weapon_off') return false
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return false
  const slug = craftedAffixCategorySlug.value
  return !!(slug && LEGENDARY_WEAPON_SLUGS.has(slug))
})

function towerSequenceRowIsEquipped(row: TowerSequenceModifierRow): boolean {
  const eq = equipped.value[selectedSlotIndex.value]
  return (eq?.craftedTowerSequenceAffixes ?? []).some(a => a.modifierId === row.modifierId)
}

function inferCraftedPropertyPickFromSlug(slotId: EquipmentSlotId, slug: string) {
  if (ARMOR_STAT_FILTER_SLOT_IDS.has(slotId)) {
    if (slug.startsWith('STR_')) return { armor: 'str' as const, ring: null, weapon: null }
    if (slug.startsWith('DEX_')) return { armor: 'dex' as const, ring: null, weapon: null }
    if (slug.startsWith('INT_')) return { armor: 'int' as const, ring: null, weapon: null }
  }
  if (RING_KIND_FILTER_SLOT_IDS.has(slotId)) {
    if (slug === 'Ring') return { armor: null, ring: 'ring' as const, weapon: null }
    if (slug === 'Spirit_Ring') return { armor: null, ring: 'spirit_ring' as const, weapon: null }
  }
  if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    return { armor: null, ring: null, weapon: slug }
  }
  return { armor: null, ring: null, weapon: null }
}

function restoreCraftedPickerStateFromSelectedEquipped() {
  if (equipmentKind.value !== 'crafted') return
  const slotId = activeSlot.value.id
  const cur = equipped.value[selectedSlotIndex.value]
  if (!cur || cur.kind !== 'crafted') return
  const slug = cur.craftedAffixCategorySlug ?? cur.craftedWeaponCategorySlug
  if (!slug) return
  const pick = inferCraftedPropertyPickFromSlug(slotId, slug)
  if (pick.armor) craftedArmorStatPick.value = pick.armor
  if (pick.ring) craftedRingKindPick.value = pick.ring
  if (pick.weapon) craftedWeaponCategoryPick.value = pick.weapon
  craftedAffixCategorySlug.value = cur.craftedAffixCategorySlug ?? slug
  craftedGearBaseId.value = cur.craftedGearBaseId ?? null
}

watch(selectedSlotIndex, () => {
  pickerQuery.value = ''
  craftedBaseSearchQuery.value = ''
  craftedArmorStatPick.value = null
  craftedRingKindPick.value = null
  craftedWeaponCategoryPick.value = null
  armorStatFilter.value = 'all'
  ringKindFilter.value = 'all'
  weaponTypeFilter.value = 'all'
  craftedAffixTypeFilter.value = 'all'
  craftedTierFilter.value = 'all'
  craftedAffixRuleHint.value = null
  craftedBaseGridCollapsed.value = false
  restoreCraftedPickerStateFromSelectedEquipped()
})

watch(equipmentKind, (next, prev) => {
  if (skipNextEquipmentKindReset.value) {
    skipNextEquipmentKindReset.value = false
    return
  }
  if (applyingEquipmentFromStore.value) return
  if (prev != null && next != null && prev !== next) {
    equipped.value = Array.from({ length: EQUIPMENT_SLOTS.length }, () => null)
    effectRollSelections.value = {}
  }
  pickerQuery.value = ''
  craftedBaseSearchQuery.value = ''
  craftedArmorStatPick.value = null
  craftedRingKindPick.value = null
  craftedWeaponCategoryPick.value = null
  armorStatFilter.value = 'all'
  ringKindFilter.value = 'all'
  weaponTypeFilter.value = 'all'
  craftedAffixTypeFilter.value = 'all'
  craftedTierFilter.value = 'all'
  craftedAffixRuleHint.value = null
  craftedBaseGridCollapsed.value = false
  restoreCraftedPickerStateFromSelectedEquipped()
})

watch(craftedAffixTypeFilter, (v, prev) => {
  if (equipmentKind.value !== 'crafted') return
  if (v !== 'all' && prev === 'all') {
    craftedBaseGridCollapsed.value = true
  } else if (v === 'all') {
    craftedBaseGridCollapsed.value = false
  }
})

watch(
  [
    equipmentKind,
    selectedSlotIndex,
    craftedWhiteBaseRowsForActiveSlot,
    craftedPropertyStepReady
  ],
  ([kind, , rows, ready]) => {
    if (kind !== 'crafted') {
      craftedAffixCategorySlug.value = null
      craftedGearBaseId.value = null
      return
    }
    if (!ready) {
      craftedAffixCategorySlug.value = null
      craftedGearBaseId.value = null
      return
    }
    if (
      craftedAffixCategorySlug.value &&
      craftedGearBaseId.value &&
      rows.some(
        r =>
          r.affixCategorySlug === craftedAffixCategorySlug.value &&
          r.baseId === craftedGearBaseId.value
      )
    ) {
      return
    }
    const cur = equipped.value[selectedSlotIndex.value]
    if (
      cur?.kind === 'crafted' &&
      cur.craftedAffixCategorySlug &&
      cur.craftedGearBaseId &&
      rows.some(
        r =>
          r.affixCategorySlug === cur.craftedAffixCategorySlug &&
          r.baseId === cur.craftedGearBaseId
      )
    ) {
      craftedAffixCategorySlug.value = cur.craftedAffixCategorySlug
      craftedGearBaseId.value = cur.craftedGearBaseId
      return
    }
    craftedAffixCategorySlug.value = null
    craftedGearBaseId.value = null
    if (rows.length === 1) {
      const r = rows[0]!
      craftedAffixCategorySlug.value = r.affixCategorySlug
      craftedGearBaseId.value = r.baseId
      syncCraftedEquippedWithCurrentBase(r)
    }
  },
  { immediate: true }
)

watch(craftedAffixTypeTabs, tabs => {
  if (equipmentKind.value !== 'crafted') return
  const ids = new Set(tabs.map(t => t.id))
  if (!ids.has(craftedAffixTypeFilter.value)) {
    craftedAffixTypeFilter.value = 'all'
  }
})

watch(
  equipped,
  nextEq => {
    const main = nextEq[WEAPON_MAIN_SLOT_INDEX]
    if (!main) return
    const leg = legendaryById.value.get(main.id)
    const leg2h = leg ? itemIsTwoHandedWeapon(leg) : false
    const craWc =
      main.kind === 'crafted'
        ? main.craftedWeaponCategorySlug ?? main.craftedAffixCategorySlug
        : undefined
    const cra2h =
      main.kind === 'crafted' && !!craWc && TWO_HANDED_WEAPON_SLUGS.has(craWc)
    if (!leg2h && !cra2h) return
    if (nextEq[WEAPON_OFF_SLOT_INDEX]) {
      const next = [...nextEq]
      next[WEAPON_OFF_SLOT_INDEX] = null
      equipped.value = next
    }
  },
  { deep: true }
)

function clearCraftedEquippedAtSelectedSlot() {
  const idx = selectedSlotIndex.value
  const cur = equipped.value[idx]
  if (cur?.kind === 'crafted') {
    const next = [...equipped.value]
    next[idx] = null
    equipped.value = next
  }
}

function setCraftedArmorStatPick(id: 'str' | 'dex' | 'int') {
  craftedArmorStatPick.value = id
  craftedAffixCategorySlug.value = null
  craftedGearBaseId.value = null
  craftedBaseSearchQuery.value = ''
  clearCraftedEquippedAtSelectedSlot()
}

function setCraftedRingKindPick(id: 'ring' | 'spirit_ring') {
  craftedRingKindPick.value = id
  craftedAffixCategorySlug.value = null
  craftedGearBaseId.value = null
  craftedBaseSearchQuery.value = ''
  clearCraftedEquippedAtSelectedSlot()
}

function setCraftedWeaponCategoryPick(slug: string) {
  craftedWeaponCategoryPick.value = slug
  craftedAffixCategorySlug.value = null
  craftedGearBaseId.value = null
  craftedBaseSearchQuery.value = ''
  clearCraftedEquippedAtSelectedSlot()
}

/** 主手为自制双手武器时清空副手 */
function nullOffHandIfMainIsCraftedTwoHanded(next: (EquippedItem | null)[]) {
  const main = next[WEAPON_MAIN_SLOT_INDEX]
  if (!main || main.kind !== 'crafted') return
  const slug = main.craftedWeaponCategorySlug ?? main.craftedAffixCategorySlug
  if (!slug || !TWO_HANDED_WEAPON_SLUGS.has(slug)) return
  next[WEAPON_OFF_SLOT_INDEX] = null
}

/** 选中打造基底后立即写入当前格装备（无需先选词缀） */
function syncCraftedEquippedWithCurrentBase(row: CraftedWhiteBasePickerRow) {
  if (equipmentKind.value !== 'crafted') return
  const idx = selectedSlotIndex.value
  const slotId = activeSlot.value.id
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return

  const next = [...equipped.value]
  const cur = next[idx]
  const slug = row.affixCategorySlug
  const baseId = row.baseId
  const iconUrl = resolveCraftedGearBaseIconUrl({
    id: row.baseId,
    iconUrl: row.iconUrl,
    cdnIconUrl: row.cdnIconUrl
  })

  if (cur?.kind === 'crafted' && cur.craftedAffixCategorySlug === slug && cur.craftedGearBaseId === baseId) {
    const craftLen = (cur.craftedAffixes ?? []).length
    const updated: EquippedItem = {
      ...cur,
      id: craftedEquipSlotId(idx),
      name: buildCraftedEquipItemName(row.name, craftLen),
      craftedGearBaseName: row.name,
      craftedAffixCategorySlug: slug,
      craftedGearBaseId: baseId,
      craftedBaseEffectLines: row.baseEffectLines,
      iconUrl: iconUrl ?? cur.iconUrl
    }
    if (slotId === 'weapon_main' || slotId === 'weapon_off') {
      updated.craftedWeaponCategorySlug = slug
    }
    next[idx] = updated
    nullOffHandIfMainIsCraftedTwoHanded(next)
    equipped.value = next
    return
  }

  const entry: EquippedItem = {
    id: craftedEquipSlotId(idx),
    name: buildCraftedEquipItemName(row.name, 0),
    kind: 'crafted',
    craftedAffixCategorySlug: slug,
    craftedGearBaseId: baseId,
    craftedGearBaseName: row.name,
    craftedBaseEffectLines: row.baseEffectLines,
    iconUrl
  }
  if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    entry.craftedWeaponCategorySlug = slug
  }
  next[idx] = entry
  nullOffHandIfMainIsCraftedTwoHanded(next)
  equipped.value = next
}

function selectCraftedWhiteBase(row: CraftedWhiteBasePickerRow) {
  if (equipmentKind.value !== 'crafted') return
  if (activeSlot.value.id === 'weapon_off' && equippedMainIsTwoHanded.value) return
  const idx = selectedSlotIndex.value
  const cur = equipped.value[idx]
  if (cur?.kind === 'crafted') {
    const catMismatch =
      cur.craftedAffixCategorySlug != null && cur.craftedAffixCategorySlug !== row.affixCategorySlug
    const baseMismatch = cur.craftedGearBaseId != null && cur.craftedGearBaseId !== row.baseId
    if (catMismatch || baseMismatch) {
      const next = [...equipped.value]
      next[idx] = null
      equipped.value = next
    }
  }
  craftedAffixCategorySlug.value = row.affixCategorySlug
  craftedGearBaseId.value = row.baseId
  craftedAffixRuleHint.value = null
  syncCraftedEquippedWithCurrentBase(row)
}

function equipCurrent(opt: PickerEquipRow) {
  if (equipmentKind.value !== 'legendary') return
  const idx = selectedSlotIndex.value
  if (idx === WEAPON_OFF_SLOT_INDEX && equippedMainIsTwoHanded.value) return
  const next = [...equipped.value]
  next[idx] = {
    id: opt.id,
    name: opt.name,
    iconUrl: opt.iconUrl,
    requiredLevel: opt.requiredLevel,
    kind: 'legendary'
  }
  if (idx === WEAPON_MAIN_SLOT_INDEX) {
    const raw = legendaryById.value.get(opt.id)
    if (raw && itemIsTwoHandedWeapon(raw)) {
      next[WEAPON_OFF_SLOT_INDEX] = null
    }
  }
  equipped.value = next
}

function equipCraftedModifier(row: CraftedModifierRow) {
  if (equipmentKind.value !== 'crafted') return
  const idx = selectedSlotIndex.value
  const slotId = activeSlot.value.id
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return
  const baseRow = craftedWhiteBaseRowsForActiveSlot.value.find(
    r =>
      r.affixCategorySlug === row.sourceSlug &&
      r.baseId === craftedGearBaseId.value
  )
  const next = [...equipped.value]
  const cur = next[idx]

  craftedAffixRuleHint.value = null

  const nextCraft = cur?.kind === 'crafted' ? [...(cur.craftedAffixes ?? [])] : []
  const nextBasic = cur?.kind === 'crafted' ? [...(cur.craftedBasicAffixes ?? [])] : []
  const nextDream = cur?.kind === 'crafted' ? [...(cur.craftedDreamAffixes ?? [])] : []
  const nextTowerSeq = cur?.kind === 'crafted' ? [...(cur.craftedTowerSequenceAffixes ?? [])] : []

  let err: string | null = null
  if (row.affixType === '基础词缀') {
    err = validateBasicAffixAdd(nextBasic, row)
  } else if (row.affixType === '美梦词缀') {
    err = validateDreamAffixAdd(nextDream, row)
  } else {
    err = validateCraftedAffixAdd(nextCraft, row)
  }

  if (err) {
    craftedAffixRuleHint.value = err
    return
  }

  const affix: CraftedEquippedAffix = {
    modifierId: row.modifierId,
    effectPlain: row.effectPlain,
    affixType: row.affixType,
    sourceSlug: row.sourceSlug,
    tier: row.tier
  }
  if (row.affixType === '基础词缀') nextBasic.push(affix)
  else if (row.affixType === '美梦词缀') nextDream.push(affix)
  else nextCraft.push(affix)

  const baseName = baseRow?.name ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseName : undefined)
  const entry: EquippedItem = {
    id: craftedEquipSlotId(idx),
    name: buildCraftedEquipItemName(baseName, nextCraft.length),
    kind: 'crafted',
    craftedAffixes: nextCraft.length ? nextCraft : undefined,
    craftedBasicAffixes: nextBasic.length ? nextBasic : undefined,
    craftedDreamAffixes: nextDream.length ? nextDream : undefined,
    craftedTowerSequenceAffixes: nextTowerSeq.length ? nextTowerSeq : undefined,
    craftedAffixCategorySlug: row.sourceSlug,
    craftedGearBaseId: craftedGearBaseId.value ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseId : undefined),
    craftedGearBaseName: baseRow?.name ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseName : undefined),
    craftedBaseEffectLines:
      baseRow?.baseEffectLines ?? (cur?.kind === 'crafted' ? cur.craftedBaseEffectLines : undefined),
    iconUrl: baseRow
      ? resolveCraftedGearBaseIconUrl({
          id: baseRow.baseId,
          iconUrl: baseRow.iconUrl,
          cdnIconUrl: baseRow.cdnIconUrl
        })
      : cur?.kind === 'crafted'
        ? cur.iconUrl
        : undefined
  }
  if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    entry.craftedWeaponCategorySlug = row.sourceSlug
  }
  next[idx] = entry
  nullOffHandIfMainIsCraftedTwoHanded(next)
  equipped.value = next
}

function equipTowerSequenceModifier(row: TowerSequenceModifierRow) {
  if (equipmentKind.value !== 'crafted') return
  const idx = selectedSlotIndex.value
  const slotId = activeSlot.value.id
  if (slotId === 'weapon_off' && equippedMainIsTwoHanded.value) return
  if (slotId !== 'weapon_main' && slotId !== 'weapon_off') return
  const cat = craftedAffixCategorySlug.value
  if (!cat || !LEGENDARY_WEAPON_SLUGS.has(cat)) return
  if (row.sourceSlug !== cat) return

  const baseRow = craftedWhiteBaseRowsForActiveSlot.value.find(
    r =>
      r.affixCategorySlug === row.sourceSlug &&
      r.baseId === craftedGearBaseId.value
  )
  const next = [...equipped.value]
  const cur = next[idx]

  craftedAffixRuleHint.value = null

  const nextCraft = cur?.kind === 'crafted' ? [...(cur.craftedAffixes ?? [])] : []
  const nextBasic = cur?.kind === 'crafted' ? [...(cur.craftedBasicAffixes ?? [])] : []
  const nextDream = cur?.kind === 'crafted' ? [...(cur.craftedDreamAffixes ?? [])] : []
  const nextTowerSeq = cur?.kind === 'crafted' ? [...(cur.craftedTowerSequenceAffixes ?? [])] : []

  const err = validateTowerSequenceAffixAdd(nextTowerSeq, row)
  if (err) {
    craftedAffixRuleHint.value = err
    return
  }

  const affix: CraftedEquippedAffix = {
    modifierId: row.modifierId,
    effectPlain: row.effectPlain,
    affixType: row.affixType,
    sourceSlug: row.sourceSlug,
    tier: row.tier,
    towerSequence: true,
    chipPattern: row.chipPattern ?? undefined
  }
  nextTowerSeq.push(affix)

  const baseName = baseRow?.name ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseName : undefined)
  const entry: EquippedItem = {
    id: craftedEquipSlotId(idx),
    name: buildCraftedEquipItemName(baseName, nextCraft.length),
    kind: 'crafted',
    craftedAffixes: nextCraft.length ? nextCraft : undefined,
    craftedBasicAffixes: nextBasic.length ? nextBasic : undefined,
    craftedDreamAffixes: nextDream.length ? nextDream : undefined,
    craftedTowerSequenceAffixes: nextTowerSeq.length ? nextTowerSeq : undefined,
    craftedAffixCategorySlug: row.sourceSlug,
    craftedGearBaseId: craftedGearBaseId.value ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseId : undefined),
    craftedGearBaseName: baseRow?.name ?? (cur?.kind === 'crafted' ? cur.craftedGearBaseName : undefined),
    craftedBaseEffectLines:
      baseRow?.baseEffectLines ?? (cur?.kind === 'crafted' ? cur.craftedBaseEffectLines : undefined),
    iconUrl: baseRow
      ? resolveCraftedGearBaseIconUrl({
          id: baseRow.baseId,
          iconUrl: baseRow.iconUrl,
          cdnIconUrl: baseRow.cdnIconUrl
        })
      : cur?.kind === 'crafted'
        ? cur.iconUrl
        : undefined
  }
  if (slotId === 'weapon_main' || slotId === 'weapon_off') {
    entry.craftedWeaponCategorySlug = row.sourceSlug
  }
  next[idx] = entry
  nullOffHandIfMainIsCraftedTwoHanded(next)
  equipped.value = next
}

function removeCraftedEquippedAffix(slotIndex: number, meta: CraftedEffectLineRemoveMeta) {
  const eq = equipped.value[slotIndex]
  if (!eq || eq.kind !== 'crafted') return
  const from: 'craft' | 'basic' | 'dream' | 'tower' =
    meta.pool === 'craft'
      ? 'craft'
      : meta.pool === 'basic'
        ? 'basic'
        : meta.pool === 'tower'
          ? 'tower'
          : 'dream'
  const next = [...equipped.value]
  next[slotIndex] = craftedEntryAfterRemovingFrom(eq, from, meta.modifierId)
  equipped.value = next
}

function clearSlotAt(index: number) {
  const next = [...equipped.value]
  next[index] = null
  equipped.value = next
}

const buildStore = useBuildStore()
const EQUIPMENT_SNAPSHOT_V = 1
const EQUIPMENT_LOCAL_STORAGE_KEY = 'torchlight:equipment:v1:standalone'
const BUILD_EQUIPMENT_FALLBACK_KEY = 'torchlight:build:v1:equipment'
const applyingEquipmentFromStore = ref(false)
const skipNextEquipmentKindReset = ref(false)
const persistenceDebug = ref({
  lastWriteStatus: 'init',
  lastWriteAtText: '',
  lastReadSource: '',
  lastReadAtText: '',
  lastAppliedEquippedCount: 0,
  standalonePayloadSize: 0,
  buildFallbackPayloadSize: 0
})

function createEquipmentSnapshotPayload() {
  return {
    v: EQUIPMENT_SNAPSHOT_V,
    savedAt: Date.now(),
    equipmentKind: equipmentKind.value,
    selectedSlotIndex: selectedSlotIndex.value,
    equipped: JSON.parse(JSON.stringify(equipped.value)),
    effectRollSelections: { ...effectRollSelections.value }
  }
}

function compactEquippedForPersistence(list: (EquippedItem | null)[]) {
  return list.map(item => {
    if (!item) return null
    if (item.kind === 'legendary') {
      return {
        kind: 'legendary' as const,
        id: item.id,
        requiredLevel: item.requiredLevel ?? undefined
      }
    }
    return {
      kind: 'crafted' as const,
      id: item.id,
      craftedAffixCategorySlug: item.craftedAffixCategorySlug ?? undefined,
      craftedWeaponCategorySlug: item.craftedWeaponCategorySlug ?? undefined,
      craftedGearBaseId: item.craftedGearBaseId ?? undefined,
      craftedGearBaseName: item.craftedGearBaseName ?? undefined,
      craftedBaseEffectLines: item.craftedBaseEffectLines ?? undefined,
      craftedAffixes: item.craftedAffixes ?? undefined,
      craftedBasicAffixes: item.craftedBasicAffixes ?? undefined,
      craftedDreamAffixes: item.craftedDreamAffixes ?? undefined,
      craftedTowerSequenceAffixes: item.craftedTowerSequenceAffixes ?? undefined
    }
  })
}

function createEquipmentSnapshotPayloadCompact() {
  return {
    v: EQUIPMENT_SNAPSHOT_V,
    savedAt: Date.now(),
    equipmentKind: equipmentKind.value,
    selectedSlotIndex: selectedSlotIndex.value,
    equipped: compactEquippedForPersistence(equipped.value),
    effectRollSelections: { ...effectRollSelections.value }
  }
}

function writeEquipmentStandaloneStorage() {
  let payload = JSON.stringify(createEquipmentSnapshotPayload())
  let standaloneOk = false
  let fallbackOk = false
  try {
    localStorage.setItem(EQUIPMENT_LOCAL_STORAGE_KEY, payload)
    standaloneOk = true
  } catch {
    try {
      payload = JSON.stringify(createEquipmentSnapshotPayloadCompact())
      localStorage.setItem(EQUIPMENT_LOCAL_STORAGE_KEY, payload)
      standaloneOk = true
    } catch {
      // ignore standalone persistence failure
    }
  }
  try {
    localStorage.setItem(BUILD_EQUIPMENT_FALLBACK_KEY, payload)
    fallbackOk = true
  } catch {
    try {
      payload = JSON.stringify(createEquipmentSnapshotPayloadCompact())
      localStorage.setItem(BUILD_EQUIPMENT_FALLBACK_KEY, payload)
      fallbackOk = true
    } catch {
      // ignore build fallback persistence failure
    }
  }
  persistenceDebug.value.lastWriteStatus =
    standaloneOk && fallbackOk ? 'ok(standalone+build)' : standaloneOk ? 'ok(standalone)' : fallbackOk ? 'ok(build)' : 'failed'
  persistenceDebug.value.lastWriteAtText = new Date().toLocaleString()
  persistenceDebug.value.standalonePayloadSize = payload.length
  persistenceDebug.value.buildFallbackPayloadSize = payload.length
}

function readEquipmentStandaloneStorage(): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(EQUIPMENT_LOCAL_STORAGE_KEY)
    if (!raw) return null
    persistenceDebug.value.standalonePayloadSize = raw.length
    const p = JSON.parse(raw)
    if (p && typeof p === 'object' && !Array.isArray(p)) return p as Record<string, unknown>
  } catch {
    // ignore invalid standalone payload
  }
  return null
}

function readBuildEquipmentFallbackStorage(): Record<string, unknown> | null {
  try {
    const raw = localStorage.getItem(BUILD_EQUIPMENT_FALLBACK_KEY)
    if (!raw) return null
    persistenceDebug.value.buildFallbackPayloadSize = raw.length
    const p = JSON.parse(raw)
    if (p && typeof p === 'object' && !Array.isArray(p)) return p as Record<string, unknown>
  } catch {
    // ignore invalid build fallback payload
  }
  return null
}

function parsePayloadSavedAt(payload: Record<string, unknown> | null): number {
  const v = payload?.savedAt
  return typeof v === 'number' && Number.isFinite(v) ? v : 0
}

function parsePayloadEquippedCount(payload: Record<string, unknown> | null): number {
  const arr = payload?.equipped
  if (!Array.isArray(arr)) return 0
  return arr.reduce((acc, item) => acc + (item == null ? 0 : 1), 0)
}

function applyEquipmentFromStore() {
  const storeRaw = buildStore.snapshot.equipment
  const storeObj =
    storeRaw && typeof storeRaw === 'object' ? (storeRaw as Record<string, unknown>) : null
  const buildFallbackObj = readBuildEquipmentFallbackStorage()
  const fallbackObj = readEquipmentStandaloneStorage()
  const candidates = [storeObj, buildFallbackObj, fallbackObj].filter(
    (x): x is Record<string, unknown> => !!x && x.v === EQUIPMENT_SNAPSHOT_V
  )
  const o =
    candidates.sort((a, b) => {
      const dt = parsePayloadSavedAt(b) - parsePayloadSavedAt(a)
      if (dt !== 0) return dt
      return parsePayloadEquippedCount(b) - parsePayloadEquippedCount(a)
    })[0] ?? null
  if (!o) return
  persistenceDebug.value.lastReadSource =
    o === storeObj ? 'buildStore.snapshot' : o === buildFallbackObj ? BUILD_EQUIPMENT_FALLBACK_KEY : EQUIPMENT_LOCAL_STORAGE_KEY
  persistenceDebug.value.lastReadAtText = new Date().toLocaleString()
  if (
    o.equipmentKind === 'legendary' ||
    o.equipmentKind === 'crafted' ||
    o.equipmentKind === null
  ) {
    // equipmentKind watch 默认会在类型切换时清空装备；恢复流程中需要跳过这一次。
    skipNextEquipmentKindReset.value = true
  }
  applyingEquipmentFromStore.value = true
  try {
    if (o.equipmentKind === 'legendary' || o.equipmentKind === 'crafted' || o.equipmentKind === null) {
      equipmentKind.value = o.equipmentKind
    }
    if (typeof o.selectedSlotIndex === 'number') {
      selectedSlotIndex.value = Math.min(
        Math.max(0, o.selectedSlotIndex),
        EQUIPMENT_SLOTS.length - 1
      )
    }
    if (Array.isArray(o.equipped) && o.equipped.length === EQUIPMENT_SLOTS.length) {
      equipped.value = o.equipped.map((x: unknown) =>
        x === null ? null : (JSON.parse(JSON.stringify(x)) as EquippedItem)
      )
      persistenceDebug.value.lastAppliedEquippedCount = equipped.value.filter(Boolean).length
    }
    if (o.effectRollSelections && typeof o.effectRollSelections === 'object') {
      effectRollSelections.value = { ...(o.effectRollSelections as Record<string, string>) }
    }
  } finally {
    applyingEquipmentFromStore.value = false
  }
}

applyEquipmentFromStore()
restoreCraftedPickerStateFromSelectedEquipped()

watch(
  [equipmentKind, selectedSlotIndex, equipped, effectRollSelections],
  () => {
    // 先写独立装备快照，避免任何后续 guard/异常导致本页数据丢失。
    writeEquipmentStandaloneStorage()
    if (applyingEquipmentFromStore.value) return
    const payload = createEquipmentSnapshotPayload()
    buildStore.setEquipment(payload)
  },
  { deep: true }
)

onMounted(applyEquipmentFromStore)
onActivated(applyEquipmentFromStore)
</script>

<style scoped>
.equipment-page {
  box-sizing: border-box;
  height: 100%;
  min-height: 0;
  max-height: 100%;
  overflow: hidden;
  padding: 18px;
  color: #fff;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.equipment-header {
  flex-shrink: 0;
  margin-bottom: 14px;
}

.equipment-header h1 {
  margin: 0 0 8px;
  font-size: 24px;
}

.equipment-header p {
  margin: 0;
  color: rgba(255, 255, 255, 0.74);
  font-size: 14px;
  line-height: 1.5;
  max-width: 720px;
}

.equipment-picker-panel .equipment-kind-bar {
  flex-shrink: 0;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px 14px;
  margin: -4px 0 14px;
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.28);
}

.equipment-kind-label {
  font-size: 13px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.equipment-kind-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.equipment-kind-tab {
  padding: 7px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.82);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.equipment-kind-tab:hover {
  border-color: rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.1);
  color: #fff;
}

.equipment-kind-tab.active {
  border-color: rgba(233, 69, 96, 0.85);
  background: rgba(233, 69, 96, 0.18);
  color: #fff;
}

.equipment-kind-tab:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.55);
  outline-offset: 2px;
}

.equipment-slots-panel--locked {
  opacity: 0.52;
  user-select: none;
}

.equipment-summary {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
  margin-bottom: 16px;
  max-width: 520px;
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

.summary-value--muted {
  font-size: 14px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.persist-debug-panel {
  margin: 0 0 12px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.2);
  padding: 8px 10px;
  font-size: 12px;
}

.persist-debug-panel summary {
  cursor: pointer;
  color: rgba(255, 255, 255, 0.84);
}

.persist-debug-grid {
  margin-top: 8px;
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 6px 10px;
  color: rgba(255, 255, 255, 0.85);
}

.equipment-layout {
  flex: 1;
  min-height: 0;
  display: grid;
  grid-template-columns: minmax(280px, 380px) minmax(0, 1fr);
  gap: 12px;
  align-items: stretch;
}

.equipment-slots-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.22);
  padding: 10px 10px 12px;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.equipment-slots-panel > .panel-section-title {
  flex-shrink: 0;
}

.panel-section-title {
  margin: 0 0 10px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.88);
  font-weight: 600;
}

.equipment-slots-grid {
  flex-shrink: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
}

.equipment-slot-cell {
  position: relative;
  min-width: 0;
}

.equipment-slot-unmount {
  position: absolute;
  top: 4px;
  right: 4px;
  z-index: 2;
  width: 22px;
  height: 22px;
  padding: 0;
  margin: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 50%;
  font-size: 16px;
  line-height: 1;
  color: rgba(255, 255, 255, 0.92);
  background: rgba(0, 0, 0, 0.55);
  box-shadow: none;
  cursor: pointer;
  transition:
    background 0.15s ease,
    color 0.15s ease;
}

.equipment-slot-unmount:hover {
  background: rgba(233, 69, 96, 0.88);
  color: #fff;
}

.equipment-slot-unmount:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.65);
  outline-offset: 2px;
}

.equipment-slot {
  display: flex;
  flex-direction: row;
  align-items: center;
  gap: 8px;
  width: 100%;
  text-align: left;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(255, 255, 255, 0.02);
  border-radius: 10px;
  padding: 8px 8px;
  color: #fff;
  cursor: pointer;
  min-height: 52px;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.equipment-slot:hover {
  border-color: rgba(233, 69, 96, 0.4);
}

.equipment-slot.active {
  border-color: rgba(233, 69, 96, 0.85);
  box-shadow: inset 0 0 0 1px rgba(233, 69, 96, 0.22);
  background: rgba(233, 69, 96, 0.08);
}

.equipment-slot.filled:not(.active) {
  border-color: rgba(52, 211, 153, 0.35);
}

.equipment-slot--off-blocked {
  opacity: 0.72;
  border-style: dashed;
  border-color: rgba(255, 255, 255, 0.14);
}

.equipment-slot-icon-wrap {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 8px;
  overflow: hidden;
  background: rgba(0, 0, 0, 0.38);
  border: 1px solid rgba(255, 255, 255, 0.12);
  display: flex;
  align-items: center;
  justify-content: center;
  box-sizing: border-box;
}

.equipment-slot-icon-wrap--empty {
  border-style: dashed;
}

.equipment-slot-thumb {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
}

.equipment-slot-placeholder {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  border: 1.5px dashed rgba(255, 255, 255, 0.28);
  opacity: 0.85;
}

.equipment-slot-text {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.equipment-slot-title {
  font-size: 11px;
  line-height: 1.25;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
}

.equipment-slot-name {
  font-size: 10px;
  line-height: 1.3;
  color: rgba(255, 255, 255, 0.62);
  word-break: break-word;
}

.equipment-effects {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.equipment-effects > .panel-section-title {
  flex-shrink: 0;
  margin-bottom: 8px;
}

.equipment-effects-empty {
  flex-shrink: 0;
  margin: 0;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(255, 255, 255, 0.45);
}

.equipment-effects-empty code {
  font-size: 10px;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.75);
}

.equipment-effects-stack {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding-right: 4px;
}

.equipment-effect-card {
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.28);
  padding: 8px 10px;
}

.equipment-effect-card-head {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 8px;
  margin-bottom: 6px;
}

.equipment-effect-slot {
  font-size: 10px;
  font-weight: 700;
  color: rgba(233, 69, 96, 0.95);
  text-transform: none;
}

.equipment-effect-name {
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.92);
}

.equipment-effect-lines {
  margin: 0;
  padding-left: 1.1em;
  font-size: 11px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.78);
}

.equipment-effect-lines li {
  margin-bottom: 3px;
}

.equipment-effect-lines li:last-child {
  margin-bottom: 0;
}

.equipment-effect-line-row {
  display: flex;
  align-items: flex-start;
  gap: 6px 8px;
}

.equipment-effect-line-main {
  flex: 1;
  min-width: 0;
}

.equipment-effect-line-unmount {
  flex-shrink: 0;
  margin: -2px 0 0;
  padding: 0 2px;
  border: none;
  background: transparent;
  color: rgba(255, 255, 255, 0.42);
  font-size: 18px;
  line-height: 1;
  cursor: pointer;
  transition: color 0.15s ease;
}

.equipment-effect-line-unmount:hover {
  color: #e94560;
}

.equipment-effect-line-unmount:focus-visible {
  outline: none;
  color: #e94560;
}

.equipment-effect-line--flavor {
  list-style-type: none;
  margin-left: -1.1em;
  margin-top: 6px;
  color: #dbb97c;
  font-style: italic;
}

.equipment-effects-missing {
  margin: 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.equipment-effects-crafted-hint {
  margin: 0;
  font-size: 11px;
  line-height: 1.45;
  color: rgba(180, 220, 255, 0.72);
}

.equipment-picker-panel {
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(0, 0, 0, 0.2);
  padding: 12px 14px;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.equipment-picker-panel > :not(.picker-list) {
  flex-shrink: 0;
}

.panel-title {
  margin: 0 0 6px;
  font-size: 15px;
  color: #f3f4f6;
}

.panel-title-row--crafted {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px 10px;
  margin: 0 0 6px;
}

.panel-title--crafted-heading {
  margin: 0;
  flex: 1;
  min-width: 0;
}

.picker-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  line-height: 1.45;
}

.picker-hint--crafted code {
  font-size: 11px;
  padding: 1px 4px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.78);
}

.picker-hint-link {
  color: rgba(147, 197, 253, 0.95);
  text-decoration: underline;
  text-underline-offset: 2px;
}

.picker-crafted-property-block {
  margin-bottom: 12px;
}

.picker-crafted-property-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.78);
}

.picker-crafted-property-tabs {
  margin-bottom: 0;
}

.picker-crafted-weapon-cat-tabs {
  max-height: 112px;
  overflow-y: auto;
  padding-right: 2px;
}

.picker-crafted-base-block {
  margin-bottom: 10px;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.picker-crafted-base-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}

.picker-crafted-base-head .picker-crafted-base-label {
  margin-bottom: 0;
}

.picker-crafted-base-label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.72);
}

.picker-crafted-base-collapse-toggle {
  flex-shrink: 0;
  padding: 4px 10px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
  color: rgba(255, 255, 255, 0.88);
  font-size: 12px;
  cursor: pointer;
  transition:
    background 0.15s ease,
    border-color 0.15s ease;
}

.picker-crafted-base-collapse-toggle:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.28);
}

.picker-crafted-base-collapse-toggle:disabled {
  opacity: 0.45;
  cursor: not-allowed;
}

.picker-crafted-base-search-row {
  margin-bottom: 8px;
}

.picker-crafted-base-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-content: flex-start;
  max-height: 280px;
  overflow-y: auto;
  padding: 2px 2px 6px 0;
}

.picker-crafted-base-grid-empty {
  flex: 1 0 100%;
  width: 100%;
  margin: 0;
}

.picker-crafted-base-card {
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 92px;
  min-height: 118px;
  padding: 8px 6px 6px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(0, 0, 0, 0.28);
  color: inherit;
  cursor: pointer;
  text-align: center;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.picker-crafted-base-card:hover:not(:disabled) {
  border-color: rgba(255, 255, 255, 0.22);
  background: rgba(255, 255, 255, 0.06);
}

.picker-crafted-base-card.active {
  border-color: rgba(233, 69, 96, 0.55);
  background: rgba(233, 69, 96, 0.14);
  box-shadow: 0 0 0 1px rgba(233, 69, 96, 0.25);
}

.picker-crafted-base-card:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.picker-crafted-base-card-icon-wrap {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 52px;
  height: 52px;
  flex-shrink: 0;
  margin-bottom: 6px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.4);
}

.picker-crafted-base-card-icon {
  width: 48px;
  height: 48px;
  object-fit: contain;
  display: block;
  border-radius: 6px;
}

.picker-crafted-base-card-icon--empty {
  width: 44px;
  height: 44px;
  border: 1px dashed rgba(255, 255, 255, 0.22);
  border-radius: 6px;
  box-sizing: border-box;
}

.picker-crafted-base-card-name {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  width: 100%;
  font-size: 11px;
  font-weight: 600;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.9);
  word-break: break-word;
  margin-bottom: 4px;
}

.picker-crafted-base-card-lv {
  font-size: 10px;
  font-weight: 600;
  line-height: 1.2;
  color: rgba(167, 243, 208, 0.88);
  margin-top: auto;
}

.picker-crafted-base-card-lv--muted {
  color: rgba(255, 255, 255, 0.35);
  font-weight: 500;
}

.picker-empty--inline {
  margin: 0 0 12px;
}

.picker-blocked-hint--soft {
  color: rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.06);
  border-color: rgba(255, 255, 255, 0.14);
}

.picker-crafted-type-tabs {
  max-height: 120px;
  overflow-y: auto;
  padding-right: 2px;
}

.picker-crafted-tier-tabs {
  max-height: 96px;
  overflow-y: auto;
  padding-right: 2px;
}

.picker-crafted-rules-hover {
  position: relative;
  z-index: 6;
  display: inline-flex;
  align-items: center;
  margin: 0 0 8px;
}

.picker-crafted-rules-hover--in-title {
  margin: 0;
  align-self: center;
}

.picker-crafted-rules-icon-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 34px;
  height: 34px;
  padding: 0;
  border: none;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.07);
  color: rgba(180, 220, 255, 0.92);
  cursor: help;
  transition:
    background 0.15s ease,
    color 0.15s ease,
    box-shadow 0.15s ease;
}

.picker-crafted-rules-icon-btn:hover,
.picker-crafted-rules-icon-btn:focus-visible {
  background: rgba(255, 255, 255, 0.12);
  color: #fff;
  outline: none;
  box-shadow: 0 0 0 2px rgba(233, 69, 96, 0.35);
}

.picker-crafted-rules-icon-svg {
  display: block;
}

.picker-crafted-rules-tooltip {
  position: absolute;
  /* 触发器在标题行右侧：右对齐，避免宽浮层向右伸出视口 */
  right: 0;
  left: auto;
  top: calc(100% + 10px);
  box-sizing: border-box;
  width: min(340px, calc(100vw - 24px));
  padding: 12px 14px;
  font-size: 13px;
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.86);
  background: rgba(22, 26, 34, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  box-shadow: 0 14px 44px rgba(0, 0, 0, 0.5);
  z-index: 40;
  opacity: 0;
  visibility: hidden;
  pointer-events: none;
  transition:
    opacity 0.16s ease,
    visibility 0.16s ease;
}

.picker-crafted-rules-hover:hover .picker-crafted-rules-tooltip,
.picker-crafted-rules-hover:focus-within .picker-crafted-rules-tooltip {
  opacity: 1;
  visibility: visible;
  pointer-events: auto;
}

.picker-crafted-rules-tooltip-p {
  margin: 0;
}

.picker-crafted-rules-tooltip strong {
  color: #fff;
  font-weight: 600;
}

.picker-crafted-slots-diag {
  margin: 0 0 8px;
  font-size: 12px;
  color: rgba(180, 220, 255, 0.88);
}

.picker-tower-inline-label {
  display: inline-block;
  margin-right: 6px;
  font-weight: 600;
  color: rgba(255, 230, 200, 0.95);
}

.picker-hint--tower-inline {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.72);
}

.picker-crafted-rule-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin: 0 0 10px;
  font-size: 13px;
  line-height: 1.45;
  color: #ffb4a8;
}

.picker-crafted-rule-hint-icon {
  flex-shrink: 0;
  margin-top: 2px;
  color: #ff8a70;
  filter: drop-shadow(0 0 6px rgba(255, 100, 80, 0.35));
}

.picker-crafted-rule-hint-icon svg {
  display: block;
}

.picker-crafted-rule-hint-text {
  flex: 1;
  min-width: 0;
}

.picker-crafted-type-tab {
  padding: 5px 9px;
  font-size: 11px;
}

.picker-item.picker-item--crafted {
  display: block;
}

.picker-item--crafted:disabled {
  opacity: 0.48;
  cursor: not-allowed;
}

.picker-crafted-effect {
  display: block;
  font-size: 13px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.92);
}

.picker-crafted-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 12px;
  margin-top: 8px;
  font-size: 11px;
  line-height: 1.35;
  color: rgba(255, 255, 255, 0.45);
}

.picker-crafted-tier {
  color: rgba(251, 191, 36, 0.95);
  font-weight: 700;
}

.picker-blocked-hint {
  margin: -6px 0 12px;
  padding: 8px 10px;
  border-radius: 8px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(251, 191, 36, 0.95);
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.28);
}

.picker-mode-hint {
  margin: 0 0 12px;
  font-size: 13px;
  line-height: 1.55;
  color: rgba(255, 255, 255, 0.62);
}

.picker-mode-hint code {
  font-size: 12px;
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(0, 0, 0, 0.35);
  color: rgba(255, 255, 255, 0.82);
}

.picker-stat-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 10px;
}

.picker-stat-tab {
  padding: 6px 12px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(255, 255, 255, 0.82);
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.picker-stat-tab:hover {
  border-color: rgba(233, 69, 96, 0.4);
  background: rgba(233, 69, 96, 0.08);
}

.picker-stat-tab.active {
  border-color: rgba(233, 69, 96, 0.75);
  background: rgba(233, 69, 96, 0.14);
  color: #fff;
}

.picker-weapon-type-tabs {
  max-height: 132px;
  overflow-y: auto;
  padding-right: 2px;
}

.picker-weapon-type-tab {
  padding: 5px 9px;
  font-size: 11px;
}

.picker-search-row {
  margin-bottom: 10px;
}

.picker-search-input {
  width: 100%;
  height: 34px;
  padding: 0 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(26, 26, 46, 0.92);
  color: rgba(255, 255, 255, 0.92);
  font-size: 13px;
  color-scheme: dark;
  box-sizing: border-box;
}

.picker-search-input::placeholder {
  color: rgba(255, 255, 255, 0.38);
}

.picker-search-input:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.45);
  outline-offset: 2px;
  border-color: rgba(233, 69, 96, 0.4);
}

.picker-list {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-right: 2px;
}

.picker-item-icon {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  border-radius: 6px;
  object-fit: contain;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.picker-item-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.picker-item-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8px;
  min-width: 0;
}

.picker-item-name-row .picker-item-name {
  min-width: 0;
}

.picker-item-stat-tag {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.2;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid transparent;
}

.picker-item-stat-tag[data-stat='力量'] {
  color: #fecaca;
  background: rgba(220, 38, 38, 0.22);
  border-color: rgba(248, 113, 113, 0.35);
}

.picker-item-stat-tag[data-stat='敏捷'] {
  color: #bbf7d0;
  background: rgba(22, 163, 74, 0.22);
  border-color: rgba(74, 222, 128, 0.35);
}

.picker-item-stat-tag[data-stat='智慧'] {
  color: #bfdbfe;
  background: rgba(37, 99, 235, 0.25);
  border-color: rgba(96, 165, 250, 0.4);
}

.picker-item-ring-tag {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.2;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid transparent;
}

.picker-item-ring-tag[data-kind='戒指'] {
  color: #fde68a;
  background: rgba(217, 119, 6, 0.22);
  border-color: rgba(251, 191, 36, 0.4);
}

.picker-item-ring-tag[data-kind='灵戒'] {
  color: #e9d5ff;
  background: rgba(126, 34, 206, 0.28);
  border-color: rgba(192, 132, 252, 0.45);
}

.picker-item-weapon-tag {
  flex-shrink: 0;
  font-size: 10px;
  font-weight: 700;
  line-height: 1.2;
  padding: 2px 7px;
  border-radius: 4px;
  border: 1px solid rgba(45, 212, 191, 0.4);
  color: #99f6e4;
  background: rgba(13, 148, 136, 0.22);
}

.picker-item-meta {
  font-size: 11px;
  line-height: 1.25;
  color: rgba(255, 255, 255, 0.52);
}

.picker-item {
  display: block;
  width: 100%;
  text-align: left;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.04);
  color: #fff;
  font-size: 13px;
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease;
}

.picker-item.picker-item--row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.picker-item--crafted .picker-item-body {
  display: flex;
  flex-direction: column;
  width: 100%;
  min-width: 0;
}

.picker-item:hover {
  border-color: rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.1);
}

.picker-item.active {
  border-color: rgba(52, 211, 153, 0.55);
  background: rgba(52, 211, 153, 0.08);
}

.picker-item-name {
  line-height: 1.35;
}

.picker-empty {
  margin: 12px 0 0;
  font-size: 13px;
  color: rgba(255, 255, 255, 0.45);
}

@media (max-width: 900px) {
  .equipment-layout {
    grid-template-columns: 1fr;
  }

  .equipment-summary {
    max-width: none;
  }
}
</style>
