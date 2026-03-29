<template>
  <div class="calc-page">
    <div class="calc-head">
      <h2>数据计算</h2>
      <div class="calc-actions">
        <button
          type="button"
          class="btn btn-secondary"
          title="从当前已持久化的 BD 快照重新载入本页 JSON 与汇总（在其他页改完数据后点此项）"
          @click="recalculateFromBuild"
        >
          重新计算
        </button>
        <button type="button" class="btn" @click="saveAllJson">保存输入</button>
        <button type="button" class="btn danger" @click="resetAll">重置全部</button>
      </div>
    </div>

    <section class="card dmg-demo">
      <h3>伤害估算（简化模型 · 演示）</h3>
      <p class="dmg-demo-hint">
        总输出 ≈ 基础伤害 × 伤害inc × 伤害more × 抗性 × 暴击 × 其他独立乘区；<strong>总 DPS</strong> = 单次期望 × 每秒次数。每秒次数 = 基础攻速或施法（次/秒）× (1+速率inc/100) × 速率more… ——
        <strong>攻击</strong>技能用<strong>攻击速度</strong>池，<strong>法术</strong>技能用<strong>施法速度</strong>池。
        <strong>攻击</strong>侧基础点伤来自装备快照约定：<strong>主手</strong>白字+该装备附加（×本地%该装备物理）；双手主手时再乘其它装备<strong>%双手武器基础伤害</strong>；另加其它格<strong>主手武器附加</strong>；<strong>法术</strong>为手填。
        <strong>持续伤害</strong>为<strong>独立模块</strong>（单独基础点伤 / inc / more / 每秒结算次数），与击中类的攻击伤害、法术伤害、异常伤害、召唤物伤害等池在解析上分离；下方「单次期望」仍表示<strong>击中</strong>，持续段见第 8 节。演示用，与游戏内可能不一致。
      </p>
      <div class="dmg-kind-row" role="group" aria-label="技能类型">
        <span class="dmg-kind-label">技能类型（自动）</span>
        <span class="dmg-kind-auto-chip">
          {{ dmgSkillKind === 'attack' ? '攻击（由已选技能解析）' : '法术（由已选技能解析）' }}
        </span>
        <label class="dmg-kind-opt">
          <input v-model="dmgUseTraitKindFallback" type="checkbox" />
          核心无法判定时按特性兜底
        </label>
        <label class="dmg-kind-opt">
          <input v-model="dmgUseTalentAuto" type="checkbox" />
          并入天赋自动解析
        </label>
        <label class="dmg-kind-opt">
          <input v-model="dmgUseMemoryAuto" type="checkbox" />
          并入追忆词条解析
        </label>
      </div>
      <div v-if="dmgUseTalentAuto" class="dmg-talent-auto">
        <span>天赋解析：击中伤害 inc +{{ format4(dmgTalentResolved.damageIncPct) }}%</span>
        <span>持续伤害 inc +{{ format4(dmgTalentResolved.dotDamageIncPct) }}%</span>
        <span>攻击速度 +{{ format4(dmgTalentResolved.attackSpeedIncPct) }}%</span>
        <span>施法速度 +{{ format4(dmgTalentResolved.castSpeedIncPct) }}%</span>
        <span class="dmg-sub">（已识别 {{ dmgTalentResolved.matchedLines }} 条，来源 {{ dmgTalentResolved.totalEffectLines }} 条效果）</span>
      </div>
      <div v-if="dmgUseMemoryAuto" class="dmg-talent-auto">
        <span>追忆解析：击中伤害 inc +{{ format4(dmgMemoryResolved.damageIncPct) }}%</span>
        <span>持续伤害 inc +{{ format4(dmgMemoryResolved.dotDamageIncPct) }}%</span>
        <span>攻击速度 +{{ format4(dmgMemoryResolved.attackSpeedIncPct) }}%</span>
        <span>施法速度 +{{ format4(dmgMemoryResolved.castSpeedIncPct) }}%</span>
        <span class="dmg-sub">（已识别 {{ dmgMemoryResolved.matchedLines }} 条，来源 {{ dmgMemoryResolved.totalEffectLines }} 条已选词缀）</span>
      </div>
      <div class="dmg-talent-auto">
        <span>技能链路：伤害 more {{ skillDerivedSummary.damageMorePctList.length }} 条</span>
        <span class="dmg-sub"
          >公式连乘共 {{ dmgBreakdown.morePctList.length }} 条（含手填与各模块「额外」解析）</span
        >
        <span>暴击值 +{{ format4(passiveCritPoolPct) }}%</span>
        <span>攻击速度 +{{ format4(skillDerivedSummary.attackSpeedIncPct) }}%</span>
        <span>施法速度 +{{ format4(skillDerivedSummary.castSpeedIncPct) }}%</span>
        <span class="dmg-sub">（被动主技能与其辅助分开统计，最终在此汇总）</span>
      </div>
      <div class="dmg-demo-stack">
        <section class="dmg-cat">
          <h4 class="dmg-cat-title">1. 基础伤害</h4>
          <p class="dmg-cat-summary">
            进入公式的点伤 <code>{{ format4(dmgBreakdown.base) }}</code>
            <span class="dmg-sub">{{
              dmgBreakdown.baseKind === 'attack' ? '（攻击 → 武器/附加合计）' : '（法术 → 手填技能基数）'
            }}</span>
          </p>
          <template v-if="dmgSkillKind === 'attack'">
            <label class="dmg-field dmg-field--wide dmg-field--check">
              <input v-model="dmgWeaponManual" type="checkbox" class="dmg-check" />
              <span>手动填写武器物理点伤（关闭则从装备栏快照自动解析）</span>
            </label>
            <label v-if="dmgWeaponManual" class="dmg-field">
              <span>武器物理点伤（手动）</span>
              <input v-model.number="dmgWeaponBaseManual" type="number" min="0" step="any" class="dmg-input" />
            </label>
            <ul v-if="dmgWeaponManual" class="dmg-src-list">
              <li class="dmg-src-li">
                <span class="dmg-src-label">手填武器物理</span>
                <code class="dmg-src-val">{{ format4(resolvedWeaponPhysicalFlat) }}</code>
              </li>
            </ul>
            <div v-else class="dmg-cat-body dmg-weapon-auto dmg-weapon-auto--flat">
              <div class="dmg-weapon-auto-title">
                攻击基础约定：<strong>主手</strong>白字 + 该装备附加物理，再乘本地 % 该装备物理伤害；主手为<strong>双手武器</strong>时，其它装备上的<strong>% 双手武器基础伤害</strong>加总后乘在该段上；武器上「攻击附加」不计入。其它装备格另计<strong>主手武器附加</strong>物理。双持时副手武器段仅作参考、<strong>不计入</strong>本页合计。
              </div>
              <div class="dmg-weapon-auto-grid">
                <span>主手 (白字+该装备附加)×本地 inc</span><code>{{ format4(weaponPhysicalEst.weaponLocalAttackBase) }}</code>
                <template
                  v-if="
                    weaponPhysicalEst.mainIsTwoHandedMelee &&
                    weaponPhysicalEst.otherSourcesTwoHandedBaseIncPctSum !== 0
                  "
                >
                  <span>其它装备「双手武器基础伤害」inc 合计</span><code
                    >{{ format4(weaponPhysicalEst.otherSourcesTwoHandedBaseIncPctSum) }}%</code
                  >
                </template>
                <span>主手武器段合计</span><code>{{ format4(weaponPhysicalEst.weaponLocalTotal) }}</code>
                <template v-if="weaponPhysicalEst.dualWield">
                  <span>副手本地（未计入合计）</span><code>{{ format4(weaponPhysicalEst.offWeaponLocalTotal) }}</code>
                </template>
                <span>用于公式的武器段</span><strong class="dmg-weapon-strike">{{
                  format4(weaponPhysicalEst.weaponStrikeAverage)
                }}</strong>
                <span>其他部位「主手武器附加」合计</span><code>{{
                  format4(weaponPhysicalEst.otherSlotsMainHandWeaponFlatSum)
                }}</code>
                <span>合计（公式用）</span><strong>{{ format4(weaponPhysicalEst.totalPhysicalFlat) }}</strong>
              </div>
              <ul v-if="weaponPhysicalEst.notes.length" class="dmg-src-list" aria-label="装备解析明细">
                <li v-for="(note, idx) in weaponPhysicalEst.notes" :key="'wpn-' + idx" class="dmg-src-li dmg-src-li--note">
                  {{ note }}
                </li>
              </ul>
              <ul
                v-if="weaponPhysicalEst.otherSlotsBySlot.length"
                class="dmg-other-slots-list"
                aria-label="各装备格主手武器附加"
              >
                <li
                  v-for="row in weaponPhysicalEst.otherSlotsBySlot"
                  :key="row.slotIndex"
                  class="dmg-other-slots-item"
                >
                  <span class="dmg-other-slots-label">{{ equipmentSlotLabel(row.slotIndex) }}</span>
                  <code>{{ format4(row.flatSum) }}</code>
                </li>
              </ul>
            </div>
          </template>
          <template v-else>
            <label class="dmg-field">
              <span>技能基础点伤（一次击中，等级/面板合并为演示数值）</span>
              <input v-model.number="dmgSpellBase" type="number" min="0" step="any" class="dmg-input" />
            </label>
            <ul class="dmg-src-list">
              <li class="dmg-src-li">
                <span class="dmg-src-label">手填法术基础点伤</span>
                <code class="dmg-src-val">{{ format4(dmgSpellBase) }}</code>
              </li>
            </ul>
          </template>
          <div class="dmg-module-total" aria-label="基础伤害合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（击中基础点伤）</span>
              <code class="dmg-module-total-val">{{ format4(dmgBreakdown.base) }}</code>
            </div>
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">2. 属性面板</h4>
          <p class="dmg-cat-hint dmg-sub">
            力量 / 敏捷 / 智慧为<strong>装备已选效果</strong>中的平加粗算合计，不含天赋加点、等级、追忆等其它来源；与下方「天赋 · …（装备粗算 …）」后缀使用同一套数值。
          </p>
          <div class="dmg-weapon-auto-grid">
            <span>力量</span>
            <code>{{ format4(buildPrimaryStatsForAnnotation.力量) }}</code>
            <span>敏捷</span>
            <code>{{ format4(buildPrimaryStatsForAnnotation.敏捷) }}</code>
            <span>智慧</span>
            <code>{{ format4(buildPrimaryStatsForAnnotation.智慧) }}</code>
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">3. 伤害提高（inc · 击中类）</h4>
          <p class="dmg-cat-hint dmg-sub">
            仅统计攻击/法术/元素等<strong>击中</strong>池；「持续伤害」「异常伤害」类 % 归入第 8 节；邻域含<strong>暴击伤害</strong>的 % 归入第 6 节，不与此处相加。
          </p>
          <p class="dmg-cat-summary">
            加法池合计 <code>{{ format4(dmgIncSourceRows.totalPct) }}%</code>
            <span class="dmg-sub">→ 乘区</span> <code>{{ format4(dmgBreakdown.increasedMultiplier) }}</code>
          </p>
          <label class="dmg-field dmg-field--wide">
            <span>手填提高类总和 %（击中池，与下方天赋/追忆自动项相加）</span>
            <input
              :value="numericInputDisplay(dmgIncreased)"
              type="number"
              step="any"
              class="dmg-input"
              @input="onDmgIncreasedInput"
            />
          </label>
          <ul class="dmg-src-list">
            <li v-for="(row, idx) in dmgIncSourceRows.rows" :key="'inc-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val">{{ formatIncRowPct(row.pct) }}</code>
            </li>
          </ul>
          <div class="dmg-module-total" aria-label="击中伤害提高合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（击中伤害提高 · 加法池）</span>
              <code class="dmg-module-total-val">{{ format4(dmgIncSourceRows.totalPct) }}%</code>
            </div>
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">4. 伤害额外（more）</h4>
          <p class="dmg-cat-hint dmg-sub">
            结算为 <strong>逐项连乘</strong> Π(1+p/100)。除手填与核心/主动/被动链路外，自动纳入：勾选并入时的<strong>天赋、追忆</strong>，以及<strong>装备全槽、契灵、英雄特性、核心与主动当前等级成长文案</strong>中邻域含「额外」、且属击中伤害池的
            %（排除持续/异常/暴击伤害专池，以及承伤类「额外」：<strong>受到的伤害</strong>、<strong>受到的物理/法术…伤害</strong>、<strong>来自…敌人的伤害</strong>等）。被动主技能上的 more 已在「技能链路」合并条目中体现，避免与文案重复计数。<strong>英雄特性</strong>来源的 more
            按特性等级缩放：默认 Lv.3，追忆词缀中「+N 英雄特性等级」与默认值相加（当前用于公式：
            <strong>Lv.{{ dmgHeroTraitEffectiveLevel }}</strong>
            <span v-if="dmgHeroTraitLevelBonusFromMemories !== 0" class="dmg-sub">
              ，追忆合计 +{{ format4(dmgHeroTraitLevelBonusFromMemories) }}</span
            >）；「每级/每 1 等级…额外」类为<strong>解析值 × 等级</strong>，其余为<strong>解析值 × (等级 / 3)</strong>。<strong>核心槽</strong>主技能若在标签中含<strong>力量/敏捷/智慧</strong>，则按装备粗算对应属性合计，以<strong>每点
            0.5% more</strong>合成为一条连乘（多标签则属性值相加后再 ×0.5%）。命中<strong>「每有 N 层 X」</strong>且后跟<strong>额外/+…% 伤害</strong>类文案的装备（及契灵）击中 more：按名称 <strong>X</strong> 从<strong>装备 + 天赋</strong>汇总「<strong>X
            层数上限</strong>」± 值与「<strong>额外拥有层数</strong>」，在基础 4 层上估算满层数；列表括号标注<strong>（X N 层）</strong>，右侧为每层加成×N。若含<strong>最多叠加 M 层</strong>则取 min(估算, M)。<strong>不限定火焰/核心标签</strong>。
          </p>
          <p class="dmg-cat-summary">
            <span class="dmg-sub">共 {{ dmgBreakdown.morePctList.length }} 条连乘 → 乘区</span>
            <code>{{ format4(dmgBreakdown.moreMultiplier) }}</code>
          </p>
          <ul class="dmg-blessing-auto-list dmg-sub" aria-label="常见祝福层数估算">
            <li v-for="row in autoBlessingStacksSummaryRows" :key="'bless-' + row.subject">
              {{ row.subject }}（装备 + 天赋 · 满层近似）：<code>{{ row.stacks }}</code>
            </li>
          </ul>
          <label class="dmg-field dmg-field--wide">
            <span>手填额外 % 列表（英文逗号分隔，各自连乘）</span>
            <input v-model="dmgMoreListStr" type="text" class="dmg-input" placeholder="例：24, 18, 12" />
          </label>
          <ul v-if="dmgMoreDisplayRows.length" class="dmg-src-list">
            <li v-for="(row, idx) in dmgMoreDisplayRows" :key="'more-' + idx" class="dmg-src-li">
              <span class="dmg-src-tag">{{ row.origin }}</span>
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val">+{{ format4(row.pct) }}%</code>
            </li>
          </ul>
          <p v-else class="dmg-cat-empty dmg-sub">暂无手填、技能链路及各模块解析项</p>
          <div class="dmg-module-total" aria-label="伤害额外合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（伤害额外 · 连乘乘区）</span>
              <code class="dmg-module-total-val">{{ format4(dmgBreakdown.moreMultiplier) }}</code>
            </div>
            <div class="dmg-module-total-line dmg-module-total-line--note">
              <span class="dmg-module-total-label">各条 % 代数和（仅供参考，结算为连乘）</span>
              <code class="dmg-module-total-val">{{ format4(dmgMorePctAlgebraicSum) }}%</code>
            </div>
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">5. 暴击值</h4>
          <p class="dmg-cat-hint dmg-sub">
            按当前技能类型（<strong>{{ dmgSkillKind === 'attack' ? '攻击' : '法术' }}</strong
            >）汇总：装备全槽、被动、天赋、追忆、英雄特性中含「暴击值 / 攻击暴击值 / 法术暴击值 / 攻击和法术暴击值」的词条；双端词条计入两侧池。底部<strong>有效暴击值</strong> = 平值加总 × (1 + %加总/100)。<strong>面板暴击率</strong> = 有效暴击值 ÷ 100（例 2230 → 22.3%）；公式内概率 = min(1, 有效 ÷ 10000)，再代入暴击期望乘区。
          </p>
          <ul class="dmg-src-list">
            <li
              v-for="(s, idx) in dmgEquipmentCritPctSourcesForPool"
              :key="'ecp-' + idx"
              class="dmg-src-li"
            >
              <span class="dmg-src-label"
                >装备 · {{ equipmentSlotLabel(s.slotIndex) }} · {{ s.snippet
                }}<template v-if="s.critScope === 'spell'">（法术）</template
                ><template v-else-if="s.critScope === 'attack'">（攻击）</template></span
              >
              <code class="dmg-src-val">+{{ format4(s.value) }}%</code>
            </li>
            <li
              v-for="(s, idx) in dmgEquipmentCritFlatSourcesForPool"
              :key="'ecf-' + idx"
              class="dmg-src-li"
            >
              <span class="dmg-src-label"
                >装备 · {{ equipmentSlotLabel(s.slotIndex) }} · {{ s.snippet
                }}<template v-if="s.critScope === 'spell'">（法术）</template
                ><template v-else-if="s.critScope === 'attack'">（攻击）</template></span
              >
              <code class="dmg-src-val">+{{ format4(s.value) }}</code>
            </li>
            <li v-for="(row, idx) in passiveCritUiRows" :key="'pcr-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val"
                ><template v-if="row.pct !== 0">+{{ format4(row.pct) }}%</template
                ><template v-if="row.pct !== 0 && row.flat !== 0"> </template
                ><template v-if="row.flat !== 0">+{{ format4(row.flat) }} 平</template></code
              >
            </li>
            <li v-for="(row, idx) in critMiscLineUiRows" :key="'cmx-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.origin }} · {{ row.label }}</span>
              <code class="dmg-src-val"
                ><template v-if="row.pct !== 0">+{{ format4(row.pct) }}%</template
                ><template v-if="row.pct !== 0 && row.flat !== 0"> </template
                ><template v-if="row.flat !== 0">+{{ format4(row.flat) }} 平</template></code
              >
            </li>
            <li v-if="critAutoSourcesEmpty" class="dmg-src-li dmg-sub">
              当前技能池下无自动解析的暴击值来源（或词条未含可识别关键词）
            </li>
          </ul>
          <div class="dmg-module-total" aria-label="暴击相关合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（暴击值 · % 加总）</span>
              <code class="dmg-module-total-val">+{{ format4(critValuePctSourcesSum) }}%</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（暴击值 · 平）</span>
              <code class="dmg-module-total-val">+{{ format4(critValueFlatSourcesSum) }}</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（暴击值 · 有效）</span>
              <code class="dmg-module-total-val"
                >{{ format4(critValueFlatSourcesSum) }} × (1 + {{ format4(critValuePctSourcesSum) }} / 100) ≈
                {{ format4(critValueEffectiveCombined) }}</code
              >
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（伤害暴击期望倍率）</span>
              <code class="dmg-module-total-val"
                >{{ format4(dmgBreakdown.critExpectedMultiplier)
                }}<span class="dmg-sub">
                  （面板暴击率 {{ format4(dmgResolvedCritChance * 100) }}% = 有效暴击值÷100，封顶 100%）</span
                ></code
              >
            </div>
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">6. 暴击伤害</h4>
          <p class="dmg-cat-hint dmg-sub">
            汇总<strong>天赋、追忆、被动、装备全槽、契灵、核心/主动成长文案、英雄特性</strong>中含「暴击伤害」「攻击暴击伤害」「法术暴击伤害」的 %（排除「暴击伤害减免」、邻域含<strong>受到的</strong>等对敌易伤类）；与击中 inc
            分离。手填 M 留空视为 1；最终倍率 = M 与解析提高%按 <code>1 + (M−1)×(1+Σ%/100)</code> 合并（演示口径）。
          </p>
          <p class="dmg-cat-summary">
            暴击时总倍率（相对不暴击） <code>{{ format4(dmgBreakdown.critStrikeMultiplier) }}</code>
          </p>
          <label class="dmg-field dmg-field--wide">
            <span>手填暴击时基础倍率 M（留空则按 1，例 2.2）</span>
            <input
              :value="numericInputDisplay(dmgCritMult)"
              type="number"
              step="any"
              class="dmg-input"
              @input="onDmgCritMultInput"
            />
          </label>
          <ul class="dmg-src-list">
            <li class="dmg-src-li">
              <span class="dmg-src-label">手填基础倍率 M</span>
              <code class="dmg-src-val">{{
                dmgCritMult != null && Number.isFinite(dmgCritMult) ? format4(dmgCritMult) : '—'
              }}</code>
            </li>
            <template v-if="dmgUseTalentAuto">
              <li
                v-for="(s, idx) in dmgTalentResolved.critDamageSources"
                :key="'cd-t-' + idx"
                class="dmg-src-li"
              >
                <span class="dmg-src-label">天赋 · {{ s.label }}{{ s.annotationSuffix ?? '' }}</span>
                <code class="dmg-src-val">+{{ format4(s.pct) }}%</code>
              </li>
            </template>
            <template v-if="dmgUseMemoryAuto">
              <li
                v-for="(s, idx) in dmgMemoryResolved.critDamageSources"
                :key="'cd-m-' + idx"
                class="dmg-src-li"
              >
                <span class="dmg-src-label">追忆 · {{ s.label }}{{ s.annotationSuffix ?? '' }}</span>
                <code class="dmg-src-val">+{{ format4(s.pct) }}%</code>
              </li>
            </template>
            <li
              v-for="(r, idx) in skillDerivedSummary.passiveCritDamageRows"
              :key="'cd-p-' + idx"
              class="dmg-src-li"
            >
              <span class="dmg-src-label">{{ r.label }}</span>
              <code class="dmg-src-val">+{{ format4(r.pct) }}%</code>
            </li>
            <li
              v-for="(r, idx) in dmgEquipmentCritDamageSourceRows"
              :key="'cd-eq-' + idx"
              class="dmg-src-li"
            >
              <span class="dmg-src-label"
                >装备 · {{ equipmentSlotLabel(r.slotIndex) }} · {{ r.snippet }}</span
              >
              <code class="dmg-src-val">+{{ format4(r.pct) }}%</code>
            </li>
            <li v-for="(r, idx) in critDamagePactLineRows" :key="'cd-pact-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ r.label }}</span>
              <code class="dmg-src-val">+{{ format4(r.pct) }}%</code>
            </li>
            <li v-for="(r, idx) in critDamageCoreActiveLineRows" :key="'cd-ca-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ r.label }}</span>
              <code class="dmg-src-val">+{{ format4(r.pct) }}%</code>
            </li>
            <li v-for="(r, idx) in critDamageHeroTraitLineRows" :key="'cd-h-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ r.label }}</span>
              <code class="dmg-src-val">+{{ format4(r.pct) }}%</code>
            </li>
          </ul>
          <div class="dmg-module-total" aria-label="暴击伤害合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（暴击伤害 · 解析提高 % 加总）</span>
              <code class="dmg-module-total-val">+{{ format4(dmgCritDamageAutoIncPct) }}%</code>
            </div>
            <!-- <div class="dmg-module-total-line dmg-module-total-line--emph">
              <span class="dmg-module-total-label">合计（暴击时伤害倍率 · 已并入公式）</span>
              <code class="dmg-module-total-val">{{ format4(dmgBreakdown.critStrikeMultiplier) }}</code>
            </div> -->
          </div>
        </section>

        <section class="dmg-cat">
          <h4 class="dmg-cat-title">7. {{ dmgSkillKind === 'attack' ? '攻击速度' : '施法速度' }}</h4>
          <p class="dmg-cat-summary">
            每秒次数 <code>{{ format4(dmgSpeedBreakdown.hitsPerSecond) }}</code>
            <span class="dmg-sub"
              >（基础 {{ format4(dmgSpeedBreakdown.basePerSecond) }} × inc 乘区
              {{ format4(dmgSpeedBreakdown.speedIncreasedMultiplier) }} × more
              {{ format4(dmgSpeedBreakdown.speedMoreMultiplier) }}）</span
            >
          </p>
          <label class="dmg-field">
            <span v-if="dmgSkillKind === 'attack'">手填基础攻击速度（次/秒）</span>
            <span v-else>手填基础施法频率（次/秒）</span>
            <input v-model.number="dmgBasePerSecond" type="number" min="0" step="any" class="dmg-input" />
          </label>
          <label v-if="dmgSkillKind === 'attack'" class="dmg-field dmg-field--wide dmg-field--check">
            <input v-model="dmgUseWeaponBaseSpeedAuto" type="checkbox" class="dmg-check" />
            <span>自动使用武器基础攻速（解析值 {{ format4(equipmentAttackStatEst.baseAttackPerSecond) }} 次/秒）</span>
          </label>
          <ul v-if="dmgSkillKind === 'attack' && dmgUseWeaponBaseSpeedAuto" class="dmg-src-list">
            <li v-for="(s, idx) in dmgEquipmentBaseApsSources" :key="'aps-' + idx" class="dmg-src-li">
              <span class="dmg-src-label"
                >武器基础攻速 · {{ equipmentSlotLabel(s.slotIndex) }} · {{ s.snippet }}</span
              >
              <code class="dmg-src-val">{{ format4(s.value) }}</code>
            </li>
            <li v-if="!dmgEquipmentBaseApsSources.length" class="dmg-src-li dmg-sub">未解析到武器「+X 攻击速度」白字</li>
          </ul>
          <label class="dmg-field dmg-field--wide">
            <span v-if="dmgSkillKind === 'attack'">手填攻击速度 inc %（与下列来源相加）</span>
            <span v-else>手填施法速度 inc %（与下列来源相加）</span>
            <input
              :value="numericInputDisplay(dmgSpeedInc)"
              type="number"
              step="any"
              class="dmg-input"
              @input="onDmgSpeedIncInput"
            />
          </label>
          <ul class="dmg-src-list">
            <li v-for="(row, idx) in dmgSpeedIncSourceRows.rows" :key="'sp-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val">{{ formatIncRowPct(row.pct) }}</code>
            </li>
          </ul>
          <label class="dmg-field dmg-field--wide">
            <span v-if="dmgSkillKind === 'attack'">手填攻击速度 more %（逗号分隔）</span>
            <span v-else>手填施法速度 more %（逗号分隔）</span>
            <input v-model="dmgSpeedMoreStr" type="text" class="dmg-input" placeholder="例：8, 12" />
          </label>
          <ul v-if="dmgHandSpeedMoreSources.length" class="dmg-src-list">
            <li v-for="(row, idx) in dmgHandSpeedMoreSources" :key="'sm-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val">+{{ format4(row.pct) }}%</code>
            </li>
          </ul>
          <div class="dmg-module-total" aria-label="攻击施法速度合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（速率提高 · 加法池）</span>
              <code class="dmg-module-total-val">{{ format4(dmgSpeedIncSourceRows.totalPct) }}%</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（速率额外 · 连乘乘区）</span>
              <code class="dmg-module-total-val">{{ format4(dmgSpeedBreakdown.speedMoreMultiplier) }}</code>
            </div>
            <div class="dmg-module-total-line dmg-module-total-line--note">
              <span class="dmg-module-total-label">手填速率 more 条 % 代数和</span>
              <code class="dmg-module-total-val">{{ format4(dmgSpeedMoreAlgebraicSum) }}%</code>
            </div>
            <div class="dmg-module-total-line dmg-module-total-line--emph">
              <span class="dmg-module-total-label">合计（每秒攻击/施法次数）</span>
              <code class="dmg-module-total-val">{{ format4(dmgSpeedBreakdown.hitsPerSecond) }}</code>
            </div>
          </div>
        </section>

        <section class="dmg-cat dmg-cat--dot">
          <h4 class="dmg-cat-title">8. 持续伤害（独立模块）</h4>
          <p class="dmg-cat-hint dmg-sub">
            与击中、异常伤害、召唤物伤害等池分离；天赋/追忆中邻域含「持续伤害」的 % 计入本节 inc。演示沿用与击中相同的抗性、独立乘区手填；暴击率与击中相同（有效暴击值÷100 为面板 %，公式内 ÷10000 为概率）。
          </p>
          <p class="dmg-cat-summary">
            持续伤害 inc 合计 <code>{{ format4(dotIncSourceRows.totalPct) }}%</code>
            <span class="dmg-sub">→ 乘区</span> <code>{{ format4(dotDmgBreakdown.increasedMultiplier) }}</code>
          </p>
          <label class="dmg-field dmg-field--wide">
            <span>持续伤害基础点伤（单次结算 / 一跳，演示用合并值）</span>
            <input v-model.number="dmgDotBase" type="number" min="0" step="any" class="dmg-input" />
          </label>
          <label class="dmg-field dmg-field--wide">
            <span>手填持续伤害提高类总和 %（与天赋/追忆「持续伤害」自动项相加）</span>
            <input
              :value="numericInputDisplay(dmgDotIncreased)"
              type="number"
              step="any"
              class="dmg-input"
              @input="onDmgDotIncreasedInput"
            />
          </label>
          <ul class="dmg-src-list">
            <li v-for="(row, idx) in dotIncSourceRows.rows" :key="'dot-inc-' + idx" class="dmg-src-li">
              <span class="dmg-src-label">{{ row.label }}</span>
              <code class="dmg-src-val">{{ formatIncRowPct(row.pct) }}</code>
            </li>
          </ul>
          <label class="dmg-field dmg-field--wide">
            <span>持续伤害额外 % 列表（英文逗号分隔，各自连乘）</span>
            <input v-model="dmgDotMoreListStr" type="text" class="dmg-input" placeholder="例：12, 8" />
          </label>
          <label class="dmg-field dmg-field--wide">
            <span>每秒结算次数（跳数/秒，× 下方单次期望 ≈ 持续 DPS）</span>
            <input v-model.number="dmgDotTicksPerSecond" type="number" min="0" step="any" class="dmg-input" />
          </label>
          <ul class="dmg-src-list">
            <li class="dmg-src-li">
              <span class="dmg-src-label">持续伤害单次期望（同式：基础×inc×more×抗性×暴击×其他）</span>
              <code class="dmg-src-val">{{ format4(dotDmgBreakdown.expectedDamage) }}</code>
            </li>
            <li class="dmg-src-li dmg-line--result">
              <span class="dmg-src-label">持续伤害 DPS（期望 × 每秒次数）</span>
              <strong class="dmg-src-val">{{ format4(dotDps) }}</strong>
            </li>
          </ul>
          <div class="dmg-module-total" aria-label="持续伤害合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（持续基础点伤）</span>
              <code class="dmg-module-total-val">{{ format4(resolvedDotBaseFlat) }}</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（持续伤害提高 · 加法池）</span>
              <code class="dmg-module-total-val">{{ format4(dotIncSourceRows.totalPct) }}%</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（持续伤害额外 · 连乘乘区）</span>
              <code class="dmg-module-total-val">{{ format4(dotMoreMultiplierOnly) }}</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（持续伤害单次期望）</span>
              <code class="dmg-module-total-val">{{ format4(dotDmgBreakdown.expectedDamage) }}</code>
            </div>
            <div class="dmg-module-total-line dmg-module-total-line--emph">
              <span class="dmg-module-total-label">合计（持续伤害 DPS）</span>
              <code class="dmg-module-total-val">{{ format4(dotDps) }}</code>
            </div>
          </div>
        </section>

        <section class="dmg-cat dmg-cat--muted">
          <h4 class="dmg-cat-title">承受与独立乘区</h4>
          <label class="dmg-field">
            <span>敌人抗性 %（0–100）</span>
            <input v-model.number="dmgResistPct" type="number" min="0" max="100" step="any" class="dmg-input" />
          </label>
          <label class="dmg-field">
            <span>其他独立乘区（默认 1）</span>
            <input v-model.number="dmgOtherMult" type="number" min="0" step="0.01" class="dmg-input" />
          </label>
          <div class="dmg-module-total" aria-label="承受与独立乘区合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（抗性承受乘区）</span>
              <code class="dmg-module-total-val">{{ format4(dmgBreakdown.resistMultiplier) }}</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（其他独立乘区）</span>
              <code class="dmg-module-total-val">{{ format4(dmgBreakdown.otherIndependentMultiplier) }}</code>
            </div>
          </div>
        </section>
      </div>
      <div class="dmg-breakdown">
        <div class="dmg-line">
          <span>基础点伤</span>
          <code>{{ format4(dmgBreakdown.base) }}</code>
          <span class="dmg-sub">{{
            dmgBreakdown.baseKind === 'attack' ? '（攻击 → 武器）' : '（法术 → 技能）'
          }}</span>
        </div>
        <div class="dmg-line">
          <span>伤害提高乘区</span><code>{{ format4(dmgBreakdown.increasedMultiplier) }}</code>
        </div>
        <div class="dmg-line">
          <span>伤害额外连乘</span><code>{{ format4(dmgBreakdown.moreMultiplier) }}</code>
          <span class="dmg-sub">（{{ dmgBreakdown.morePctList.length }} 条）</span>
        </div>
        <div class="dmg-line">
          <span>抗性承受</span><code>{{ format4(dmgBreakdown.resistMultiplier) }}</code>
        </div>
        <div class="dmg-line">
          <span>暴击期望</span><code>{{ format4(dmgBreakdown.critExpectedMultiplier) }}</code>
          <span class="dmg-sub">（面板暴击率 {{ format4(dmgResolvedCritChance * 100) }}%）</span>
        </div>
        <div class="dmg-line">
          <span>其他独立乘区</span><code>{{ format4(dmgBreakdown.otherIndependentMultiplier) }}</code>
        </div>
        <div class="dmg-line dmg-line--result">
          <span>合计（击中 · 单次期望伤害）</span>
          <strong>{{ format4(dmgBreakdown.expectedDamage) }}</strong>
        </div>
      </div>
      <div class="dmg-breakdown dmg-breakdown--speed">
        <div class="dmg-line">
          <span>基础每秒次数</span><code>{{ format4(dmgSpeedBreakdown.basePerSecond) }}</code>
        </div>
        <div class="dmg-line">
          <span>速率 inc 乘区</span><code>{{ format4(dmgSpeedBreakdown.speedIncreasedMultiplier) }}</code>
        </div>
        <div class="dmg-line">
          <span>速率 more 连乘</span><code>{{ format4(dmgSpeedBreakdown.speedMoreMultiplier) }}</code>
          <span class="dmg-sub">（{{ dmgSpeedBreakdown.speedMorePctList.length }} 条）</span>
        </div>
        <div class="dmg-line">
          <span>每秒次数（{{ dmgSkillKind === 'attack' ? '攻击' : '施法' }}）</span>
          <strong>{{ format4(dmgSpeedBreakdown.hitsPerSecond) }}</strong>
        </div>
        <div class="dmg-line dmg-line--result">
          <span>合计（击中 · 总 DPS）</span>
          <strong class="dmg-dps-val">{{ format4(dmgDps.dps) }}</strong>
        </div>
      </div>
      <div v-if="showAngerBurstPanel" class="dmg-breakdown dmg-breakdown--anger">
        <div class="dmg-line">
          <span>怒火爆裂并入 DPS</span>
          <label class="dmg-kind-opt">
            <input v-model="angerBurstIncludeInDps" type="checkbox" />
            计入
          </label>
        </div>
        <p class="dmg-sub">爆裂参数使用当前构筑自动解析（装备攻速等），不在此手动修改。</p>
        <div class="dmg-line">
          <span>爆裂单次期望</span><code>{{ format4(angerBurstBreakdown.singleExpectedDamage) }}</code>
          <span class="dmg-sub">（已含怒气+怒火/顾此失彼/暴怒原罪增伤）</span>
        </div>
        <div class="dmg-line">
          <span>爆裂频率（受命中与冷却双约束）</span>
          <code>{{ format4(angerBurstBreakdown.triggersPerSecond) }}/s</code>
          <span class="dmg-sub"
            >基础 CD {{ format4(BURST_BASE_CD_SEC) }}s → 有效 {{ format4(angerBurstBreakdown.intervalSec) }}s</span
          >
        </div>
        <div class="dmg-line">
          <span>爆裂 DPS</span><code>{{ format4(angerBurstBreakdown.burstDps) }}</code>
          <span class="dmg-sub" v-if="!angerBurstIncludeInDps">（当前未并入总 DPS）</span>
        </div>
        <div class="dmg-line">
          <span>主技能 DPS（顾此失彼后）</span>
          <code>{{ format4(angerBurstBreakdown.mainSkillDpsAfterPenalty) }}</code>
          <span class="dmg-sub">（非爆裂技能 -80%）</span>
        </div>
        <div class="dmg-line dmg-line--result">
          <span>合计（怒火爆裂 · 总 DPS）</span>
          <strong class="dmg-dps-val">{{ format4(angerBurstBreakdown.totalDpsWithBurst) }}</strong>
        </div>
      </div>

      <div class="dmg-breakdown dmg-breakdown--conversion">
        <h3 class="dmg-conversion-heading">伤害转化（多来源 · 独立模块）</h3>
        <p class="dmg-sub">
          从装备已选效果、天赋已加点原文、追忆、契灵词条、英雄已选特性等解析「X% … 转化为 …」或「… 转化为 …」；<strong>不参与</strong>上方单次期望
          / DPS 连乘，与 inc/more/基础点伤分离，仅作构筑核对。
        </p>
        <template v-if="dmgConversionEst.hasAny">
          <p class="dmg-conversion-summary dmg-sub">
            共解析 <strong>{{ dmgConversionEst.segmentCount }}</strong> 条转化（{{ dmgConversionEst.entries.length }} 个来源区块）
          </p>
          <div
            v-for="ent in dmgConversionEst.entries"
            :key="'conv-' + ent.id"
            class="dmg-conversion-slot"
          >
            <div class="dmg-conversion-slot-title">{{ ent.label }}</div>
            <ul class="dmg-conversion-seg-list">
              <li v-for="(seg, si) in ent.segments" :key="'s' + si" class="dmg-conversion-seg">
                <code class="dmg-conversion-pct">{{
                  seg.pct != null ? `${format4(seg.pct)}%` : '未标%'
                }}</code>
                <span class="dmg-conversion-from" :title="seg.fromSnippet">{{ seg.fromSnippet }}</span>
                <span class="dmg-conversion-kw">转化为</span>
                <span class="dmg-conversion-to" :title="seg.toSnippet">{{ seg.toSnippet }}</span>
              </li>
            </ul>
            <ul class="dmg-src-list dmg-conversion-raw" aria-label="该格原文">
              <li
                v-for="(sl, li) in ent.sourceLines"
                :key="'ln-' + li"
                class="dmg-src-li dmg-src-li--note"
              >
                {{ sl }}
              </li>
            </ul>
          </div>
          <div class="dmg-module-total dmg-module-total--conversion" aria-label="伤害转化合计">
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（转化片段条数）</span>
              <code class="dmg-module-total-val">{{ format4(dmgConversionEst.segmentCount) }}</code>
            </div>
            <div class="dmg-module-total-line">
              <span class="dmg-module-total-label">合计（来源区块数）</span>
              <code class="dmg-module-total-val">{{ format4(dmgConversionEst.entries.length) }}</code>
            </div>
          </div>
        </template>
        <p v-else class="dmg-sub">当前各来源（装备 / 天赋 / 追忆 / 契灵 / 英雄特性等）未解析到伤害转化词条。</p>
      </div>
    </section>

    <div class="calc-json-block">
      <details class="calc-raw-json">
        <summary>原始 JSON（编辑后点「保存输入」写回存档）</summary>
        <div class="calc-grid calc-grid--raw">
          <section class="card">
            <h3>英雄</h3>
            <textarea v-model="heroJson" class="editor" spellcheck="false" />
          </section>
          <section class="card">
            <h3>技能</h3>
            <textarea v-model="skillsJson" class="editor" spellcheck="false" />
          </section>
          <section class="card">
            <h3>装备</h3>
            <textarea v-model="equipmentJson" class="editor" spellcheck="false" />
          </section>
          <section class="card">
            <h3>契灵</h3>
            <textarea v-model="pactspiritJson" class="editor" spellcheck="false" />
          </section>
          <section class="card">
            <h3>天赋（只读快照）</h3>
            <pre class="readout">{{ talentSummaryText }}</pre>
          </section>
          <section class="card">
            <h3>追忆（只读快照）</h3>
            <pre class="readout">{{ memoriesSummaryText }}</pre>
          </section>
        </div>
      </details>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onActivated, onMounted, ref, watch } from 'vue'
import { storeToRefs } from 'pinia'
import { useBuildStore, type MemorySelectionItem, flattenMemories } from '@/stores/build'
import { useProfessionTalentStore } from '@/stores/professionTalent'
import {
  effectiveBaseFlatDamage,
  estimateDps,
  estimateExpectedHitDamage,
  estimateHitsPerSecond,
  moreMultiplierFromList,
  type SkillBaseDamageKind
} from '@/utils/torchlightDamageModel'
import { perPointPrimaryAnnotationSuffix } from '@/utils/primaryStatAnnotation'
import {
  estimateAttackStatsFromEquipmentDetailed,
  estimatePhysicalAttackFlatFromEquipment,
  estimatePrimaryStatFlatFromEquipment,
  getResolvedEffectLinesForEquipmentSlot,
  parseCritContributionsFromEffectLine,
  type CritContribution,
  type CritValueScope
} from '@/utils/weaponPhysicalFromEquipment'
import {
  estimateDamageConversionFromSourceBundles,
  type DamageConversionSourceBundle
} from '@/utils/damageConversionFromEquipment'
import {
  BURST_BASE_CD_SEC,
  effectiveBurstIntervalSec,
  totalAngerDamageBonusPct
} from '@/utils/heroAngerBurst'
import heroesJson from '@/data/heroes/heroes.json'
import pactspiritCatalogJson from '@/data/pactspirit.json'
import activeSkillTagsData from '@/data/skills/activeSkillTags.json'
import supportSkillTagsData from '@/data/skills/supportSkillTags.json'
import nobleSupportSkillTagsData from '@/data/skills/nobleSupportSkillTags.json'
import magnificentSupportSkillTagsData from '@/data/skills/magnificentSupportSkillTags.json'
import passiveSkillTagsData from '@/data/skills/passiveSkillTags.json'

const buildStore = useBuildStore()
const professionTalentStore = useProfessionTalentStore()
const { snapshot } = storeToRefs(buildStore)

const EQUIPMENT_SLOT_LABELS = [
  '头部',
  '上衣',
  '项链',
  '手套',
  '腰带',
  '鞋子',
  '戒指1',
  '戒指2',
  '主武器',
  '副武器'
] as const

function equipmentSlotLabel(i: number): string {
  return EQUIPMENT_SLOT_LABELS[i] ?? `槽位 ${i}`
}

const SKILLS_SNAPSHOT_V = 1
const EQUIPMENT_SNAPSHOT_V = 1
const PACTSPIRIT_SNAPSHOT_V = 1
const HERO_SNAPSHOT_V = 1

type HeroCatalogEntry = {
  id?: string
  displayName?: string
  traitTitle?: string
  heroName?: string
  portrait?: string
  traits?: { name?: string; requiredLevel?: number; effects?: string[] }[]
}

function buildSkillIdNameMap(): Map<string, string> {
  const m = new Map<string, string>()
  const add = (arr: { id?: unknown; name?: unknown }[] | undefined) => {
    for (const it of arr ?? []) {
      const id = String(it.id ?? '').trim()
      if (!id) continue
      m.set(id, String(it.name ?? id))
    }
  }
  add(activeSkillTagsData.activeSkills as { id?: unknown; name?: unknown }[])
  add(supportSkillTagsData.supportSkills as { id?: unknown; name?: unknown }[])
  add(nobleSupportSkillTagsData.supportSkills as { id?: unknown; name?: unknown }[])
  add(magnificentSupportSkillTagsData.supportSkills as { id?: unknown; name?: unknown }[])
  add(passiveSkillTagsData.passiveSkills as { id?: unknown; name?: unknown }[])
  return m
}

const skillIdToName = buildSkillIdNameMap()
const activeSkillTagById = (() => {
  const m = new Map<string, string[]>()
  const list = (activeSkillTagsData as { activeSkills?: { id?: unknown; tags?: unknown }[] }).activeSkills ?? []
  for (const it of list) {
    const id = String(it.id ?? '').trim()
    if (!id) continue
    const tags = Array.isArray(it.tags) ? it.tags.map(x => String(x ?? '').trim()).filter(Boolean) : []
    m.set(id, tags)
  }
  return m
})()

/** 主动/核心技能等级成长文案（逐条，供暴击伤害等从技能描述解析） */
const activeSkillGrowthLinesById = (() => {
  const m = new Map<string, string[]>()
  const list =
    (
      activeSkillTagsData as {
        activeSkills?: { id?: unknown; damageMultiplierByLevel?: unknown }[]
      }
    ).activeSkills ?? []
  for (const sk of list) {
    const id = String(sk.id ?? '').trim()
    const arr = sk.damageMultiplierByLevel
    if (!id || !Array.isArray(arr)) continue
    const lines = arr.map(x => String(x ?? '').trim()).filter(Boolean)
    if (lines.length) m.set(id, lines)
  }
  return m
})()

const heroIdToDisplayName = (() => {
  const list = heroesJson as { id?: string; displayName?: string }[]
  const m = new Map<string, string>()
  for (const h of list) {
    const id = String(h.id ?? '').trim()
    if (!id) continue
    m.set(id, String(h.displayName ?? id))
  }
  return m
})()

const pactIdToName = (() => {
  const items = (pactspiritCatalogJson as { items?: { id?: string; name?: string }[] }).items ?? []
  const m = new Map<string, string>()
  for (const it of items) {
    const id = String(it.id ?? '').trim()
    if (!id) continue
    m.set(id, String(it.name ?? id))
  }
  return m
})()

function skillLabel(id: string): string {
  const t = String(id ?? '').trim()
  if (!t) return '—'
  return skillIdToName.get(t) ?? t
}

function memoryAffixKey(row: MemorySelectionItem): string {
  return String(row.modifierId ?? `${row.sourceId}|${row.effectText}|${row.tierLabel ?? ''}`)
}

/** 与其它页一致：直接读 Pinia 快照，避免「仅依赖 heroJson 文本」时 store 已更新但界面不刷新 */
const previewHero = computed(() => snapshot.value.hero as Record<string, unknown>)
const previewSkills = computed(() => snapshot.value.skills as Record<string, unknown>)
const previewEquipment = computed(() => snapshot.value.equipment as Record<string, unknown>)
const previewPact = computed(() => snapshot.value.pactspirit as Record<string, unknown>)

const previewHeroId = computed(() => String(previewHero.value.activeHeroId ?? '').trim())

const heroDisplayName = computed(() => {
  const id = previewHeroId.value
  if (!id) return '—'
  return heroIdToDisplayName.get(id) ?? id
})

const heroCatalogEntry = computed((): HeroCatalogEntry | null => {
  const id = previewHeroId.value
  if (!id) return null
  const list = heroesJson as HeroCatalogEntry[]
  return list.find(h => String(h.id ?? '').trim() === id) ?? null
})

const heroCatalogPortrait = computed(() => {
  const p = heroCatalogEntry.value?.portrait
  return typeof p === 'string' && p.trim() ? p.trim() : ''
})

/** 特性标题 · 英雄名，与英雄页卡片头部一致 */
const heroCatalogSubtitle = computed(() => {
  const e = heroCatalogEntry.value
  if (!e) return ''
  const title = String(e.traitTitle ?? '').trim()
  const name = String(e.heroName ?? '').trim()
  if (title && name) return `${title} · ${name}`
  return title || name || ''
})

const heroSnapshotWarn = computed(() => {
  const h = previewHero.value
  if (!h || typeof h !== 'object') return '英雄快照无效或为空'
  if (h.v !== HERO_SNAPSHOT_V) return `英雄快照版本非 v${HERO_SNAPSHOT_V}，以下为尽力解析`
  return ''
})

const heroTraitPickSummary = computed(() => {
  const picked = heroPreviewRows.value.length
  const tiers = heroCatalogEntry.value?.traits?.length ?? 0
  if (tiers > 0) return `已选特性：${picked} / ${tiers} 个需求等级档位`
  return `已选特性：${picked} 项`
})

const heroPreviewRows = computed(() => {
  const raw = previewHero.value.selectedTraitByRequiredLevel
  if (!raw || typeof raw !== 'object') return []
  const rows: { level: number; name: string }[] = []
  for (const [k, v] of Object.entries(raw as Record<string, unknown>)) {
    const lvl = Number(k)
    if (!Number.isFinite(lvl)) continue
    const name = String(v ?? '').trim()
    if (!name) continue
    rows.push({ level: lvl, name })
  }
  rows.sort((a, b) => a.level - b.level)
  return rows
})

type SkillLinkPreview = {
  mainSkillId?: string
  mainSkillLevel?: number
  supportSkillIds?: string[]
  supportSkillLevels?: number[]
  supportExclusiveCustomBonuses?: string[]
}

function normalizeSkillLink(x: unknown): SkillLinkPreview {
  if (!x || typeof x !== 'object') return {}
  const o = x as Record<string, unknown>
  const main = String(o.mainSkillId ?? '').trim()
  const sup = Array.isArray(o.supportSkillIds)
    ? o.supportSkillIds.map(s => String(s ?? '').trim())
    : []
  const mainLevelRaw = Number(o.mainSkillLevel)
  const mainLevel = Number.isFinite(mainLevelRaw) ? Math.max(1, Math.floor(mainLevelRaw)) : 20
  const lv = Array.isArray(o.supportSkillLevels)
    ? o.supportSkillLevels.map(v => {
        const n = Number(v)
        return Number.isFinite(n) ? Math.max(1, Math.floor(n)) : 20
      })
    : []
  const customs = Array.isArray(o.supportExclusiveCustomBonuses)
    ? o.supportExclusiveCustomBonuses.map(v => String(v ?? '').trim())
    : []
  return {
    mainSkillId: main || undefined,
    mainSkillLevel: mainLevel,
    supportSkillIds: sup,
    supportSkillLevels: lv,
    supportExclusiveCustomBonuses: customs
  }
}

/** 核心槽主技能是否带「哨卫」标签（activeSkillTags）；用于决定是否把哨卫类词条计入玩家伤害解析 */
function coreSkillIsSentryType(skills: Record<string, unknown>): boolean {
  if (!skills || typeof skills !== 'object') return false
  if (Number(skills.v) !== SKILLS_SNAPSHOT_V) return false
  const core = normalizeSkillLink(skills.core)
  const id = String(core.mainSkillId ?? '').trim()
  if (!id) return false
  return (activeSkillTagById.get(id) ?? []).includes('哨卫')
}

const skillsPreviewWarn = computed(() => {
  const s = previewSkills.value
  if (!s || typeof s !== 'object') return '技能快照无效'
  if (s.v !== SKILLS_SNAPSHOT_V) return `技能快照版本非 v${SKILLS_SNAPSHOT_V}，以下为尽力解析`
  return ''
})

const skillsLinkSlots = computed(() => {
  const s = previewSkills.value
  const core = normalizeSkillLink(s.core)
  const active = Array.isArray(s.active) ? s.active.map(normalizeSkillLink) : []
  const passive = Array.isArray(s.passive) ? s.passive.map(normalizeSkillLink) : []
  const out: {
    key: string
    label: string
    mainId: string
    supportIds: string[]
  }[] = []
  out.push({
    key: 'core',
    label: '核心',
    mainId: core.mainSkillId ?? '',
    supportIds: core.supportSkillIds ?? []
  })
  for (let i = 0; i < 4; i++) {
    const sl = active[i] ?? {}
    out.push({
      key: `a${i}`,
      label: `主动 ${i + 1}`,
      mainId: sl.mainSkillId ?? '',
      supportIds: sl.supportSkillIds ?? []
    })
  }
  for (let i = 0; i < 4; i++) {
    const sl = passive[i] ?? {}
    out.push({
      key: `p${i}`,
      label: `被动 ${i + 1}`,
      mainId: sl.mainSkillId ?? '',
      supportIds: sl.supportSkillIds ?? []
    })
  }
  return out
})

const skillsAnyPicked = computed(() =>
  skillsLinkSlots.value.some(s => Boolean(s.mainId) || s.supportIds.some(Boolean))
)

const skillsSelectedSlotText = computed(() => {
  const s = previewSkills.value
  const ss = s.selectedSlot
  if (!ss || typeof ss !== 'object') return ''
  const role = (ss as { role?: string }).role
  const index = (ss as { index?: number }).index
  if (role !== 'core' && role !== 'active' && role !== 'passive') return ''
  const idx = typeof index === 'number' && index >= 0 ? index : 0
  const label =
    role === 'core' ? '核心' : role === 'active' ? `主动 ${idx + 1}` : `被动 ${idx + 1}`
  return `界面选中槽位：${label}`
})

type EquipSlotRow = {
  index: number
  slotLabel: string
  empty: boolean
  name: string
  kind: 'legendary' | 'crafted' | ''
  affixHint: string
  effectChips: string[]
}

const equipmentPreviewWarn = computed(() => {
  const o = previewEquipment.value
  if (!o || typeof o !== 'object') return '装备快照无效'
  if (o.v !== EQUIPMENT_SNAPSHOT_V) return `装备快照版本非 v${EQUIPMENT_SNAPSHOT_V}，以下为尽力解析`
  return ''
})

const equipmentSlotRows = computed((): EquipSlotRow[] => {
  const o = previewEquipment.value
  const equipped = Array.isArray(o.equipped) ? o.equipped : []
  const rows: EquipSlotRow[] = []
  for (let i = 0; i < EQUIPMENT_SLOT_LABELS.length; i++) {
    const slotLabel = EQUIPMENT_SLOT_LABELS[i]!
    const cell = equipped[i]
    if (cell == null) {
      rows.push({
        index: i,
        slotLabel,
        empty: true,
        name: '',
        kind: '',
        affixHint: '',
        effectChips: []
      })
      continue
    }
    if (typeof cell !== 'object') {
      rows.push({
        index: i,
        slotLabel,
        empty: true,
        name: '',
        kind: '',
        affixHint: '',
        effectChips: []
      })
      continue
    }
    const eq = cell as Record<string, unknown>
    const name = String(eq.name ?? eq.id ?? '（未命名）').trim() || '（未命名）'
    const kind = eq.kind === 'crafted' ? 'crafted' : 'legendary'
    const resolved = getResolvedEffectLinesForEquipmentSlot(o, i)
    const affixHint = resolved.length ? `已选效果 ${resolved.length} 条` : '（无词条文本）'
    let effectChips: string[] = []
    if (resolved.length) {
      effectChips = resolved.slice(0, 8)
      if (resolved.length > 8) effectChips.push(`… 共 ${resolved.length} 条`)
    }
    rows.push({
      index: i,
      slotLabel,
      empty: false,
      name,
      kind,
      affixHint,
      effectChips
    })
  }
  return rows
})

const pactPreviewWarn = computed(() => {
  const p = previewPact.value
  if (!p || typeof p !== 'object') return '契灵快照无效'
  if (p.v !== PACTSPIRIT_SNAPSHOT_V) return `契灵快照版本非 v${PACTSPIRIT_SNAPSHOT_V}，以下为尽力解析`
  return ''
})

const pactBattleNames = computed(() => {
  const p = previewPact.value
  const ids = Array.isArray(p.selectedBattleIds) ? p.selectedBattleIds : []
  return ids.map(x => pactIdToName.get(String(x)) ?? String(x))
})

const pactDropNames = computed(() => {
  const p = previewPact.value
  const ids = Array.isArray(p.selectedDropIds) ? p.selectedDropIds : []
  return ids.map(x => pactIdToName.get(String(x)) ?? String(x))
})

const talentAllocatedEffects = computed(() =>
  professionTalentStore
    .getAllocatedEffects()
    .map(x => stripHtmlLikeText(String(x ?? '')))
    .filter(Boolean)
)

const memoriesFlat = computed(() => flattenMemories(buildStore.snapshot.memories))
const memoryBaseChips = computed(() =>
  memoriesFlat.value.bases.map(b => `${b.tierLabel || '—'} ${b.effectText}`.trim())
)

/** 演示：简化伤害公式输入（技能类型自动解析） */
/** 勾选后用手填值；关闭时武器物理点伤来自装备快照解析 */
const dmgWeaponManual = ref(false)
const dmgWeaponBaseManual = ref(0)
const dmgSpellBase = ref(1200)
const dmgIncreased = ref<number | null>(null)
const dmgMoreListStr = ref('')
const dmgCritMult = ref<number | null>(null)
const dmgResistPct = ref(40)
const dmgOtherMult = ref(1)
/** 持续伤害独立模块（与击中类 inc 解析分离） */
const dmgDotBase = ref(0)
const dmgDotIncreased = ref<number | null>(null)
const dmgDotMoreListStr = ref('')
const dmgDotTicksPerSecond = ref(1)
const dmgBasePerSecond = ref(1.5)
const dmgSpeedInc = ref<number | null>(null)
const dmgSpeedMoreStr = ref('')

function onDmgIncreasedInput(ev: Event) {
  dmgIncreased.value = parseOptionalNumberInput((ev.target as HTMLInputElement).value)
}
function onDmgSpeedIncInput(ev: Event) {
  dmgSpeedInc.value = parseOptionalNumberInput((ev.target as HTMLInputElement).value)
}
function onDmgDotIncreasedInput(ev: Event) {
  dmgDotIncreased.value = parseOptionalNumberInput((ev.target as HTMLInputElement).value)
}
function onDmgCritMultInput(ev: Event) {
  dmgCritMult.value = parseOptionalNumberInput((ev.target as HTMLInputElement).value)
}
const dmgUseWeaponBaseSpeedAuto = ref(true)
const dmgUseTraitKindFallback = ref(false)
const dmgUseTalentAuto = ref(true)
const dmgUseMemoryAuto = ref(true)
const angerBurstIncludeInDps = ref(true)
const angerApplyNonBurstPenalty = ref(true)

function inferSkillKindBySkillId(skillId: string): SkillBaseDamageKind | null {
  const id = String(skillId ?? '').trim()
  if (!id) return null
  const tags = activeSkillTagById.get(id) ?? []
  if (tags.includes('攻击')) return 'attack'
  if (tags.includes('法术')) return 'spell'
  const name = skillLabel(id)
  if (name.includes('爆裂') || name.includes('旋风斩')) return 'attack'
  return null
}

const coreMainSkillId = computed(() => {
  const s = previewSkills.value
  return normalizeSkillLink(s.core).mainSkillId ?? ''
})

function inferSkillKindByHeroOutputTrait(): SkillBaseDamageKind | null {
  const rows = heroPreviewRows.value
  for (const row of rows) {
    const n = String(row.name ?? '')
    // 目前已确认的「特性输出技能」优先按攻击池处理
    if (n.includes('怒火') || n.includes('爆裂') || n.includes('旋风斩')) return 'attack'
    if (n.includes('法术')) return 'spell'
  }
  return null
}

const dmgSkillKind = computed<SkillBaseDamageKind>(() => {
  // 仅看核心技能
  const coreId = coreMainSkillId.value
  const fromCore = inferSkillKindBySkillId(coreId)
  if (fromCore) return fromCore
  if (coreId.includes('Whirlwind') || coreId.includes('Burst')) return 'attack'

  // 仅在用户明确开启时，才按特性做兜底。
  if (dmgUseTraitKindFallback.value) {
    const fromTrait = inferSkillKindByHeroOutputTrait()
    if (fromTrait) return fromTrait
  }

  return 'attack'
})

function parseMoreList(s: string): number[] {
  return s
    .split(/[,，]/)
    .map(x => parseFloat(x.trim()))
    .filter(n => Number.isFinite(n))
}

function splitNumericListParts(s: string): { index: number; value: number }[] {
  const raw = s.split(/[,，]/)
  const out: { index: number; value: number }[] = []
  for (let i = 0; i < raw.length; i++) {
    const n = parseFloat(raw[i]!.trim())
    if (Number.isFinite(n)) out.push({ index: i + 1, value: n })
  }
  return out
}

/** 手填数字可为空：空串 → null，计算侧按非有限值当 0 */
function numericInputDisplay(v: number | null | undefined): string {
  if (v == null || !Number.isFinite(v)) return ''
  return String(v)
}

function parseOptionalNumberInput(raw: string): number | null {
  const t = raw.trim()
  if (t === '' || t === '+' || t === '-') return null
  const n = Number(t)
  return Number.isFinite(n) ? n : null
}

const dmgHandMoreSources = computed(() =>
  splitNumericListParts(dmgMoreListStr.value).map(({ index, value }) => ({
    label: `手填「额外 % 列表」第 ${index} 项`,
    pct: value
  }))
)

const dmgHandSpeedMoreSources = computed(() =>
  splitNumericListParts(dmgSpeedMoreStr.value).map(({ index, value }) => ({
    label: `手填「速率 more 列表」第 ${index} 项`,
    pct: value
  }))
)

function parseFirstPercentValue(s: string): number | null {
  const m = String(s ?? '').match(/([+-]?\d+(?:\.\d+)?)\s*%/)
  if (!m) return null
  const n = Number(m[1])
  return Number.isFinite(n) ? n : null
}

function parsePercentByKeywords(
  text: string | null | undefined,
  keywords: readonly string[],
  /** 邻域含任一则该 % 跳过（如被动里「伤害」会误匹配「暴击伤害」） */
  excludeAroundIncludesAny?: readonly string[]
): number | null {
  const t = String(text ?? '')
    .replace(/\s+/g, '')
    .trim()
  if (!t) return null
  const re = /([+-]?\d+(?:\.\d+)?)%/g
  let m: RegExpExecArray | null = null
  while ((m = re.exec(t)) != null) {
    const n = Number(m[1])
    if (!Number.isFinite(n)) continue
    const idx = m.index
    const around = t.slice(Math.max(0, idx - 20), Math.min(t.length, idx + m[0].length + 20))
    if (excludeAroundIncludesAny?.some(s => around.includes(s))) continue
    if (keywords.some(k => around.includes(k))) return n
  }
  return null
}

/** 与 SkillLinkCard：普通辅助 40 级表 + 崇高/华贵 T0–T2 三档可并存 */
type SupportDmgMeta = { byLevel: string[] | null; byTier: string[] | null }
const supportDmgMetaById = (() => {
  const m = new Map<string, SupportDmgMeta>()
  const merge = (
    arr:
      | {
          id?: unknown
          supportDamageBonusByLevel?: unknown
          supportDamageBonusByTier?: unknown
        }[]
      | undefined
  ) => {
    for (const it of arr ?? []) {
      const id = String(it.id ?? '').trim()
      if (!id) continue
      const byLevel = Array.isArray(it.supportDamageBonusByLevel)
        ? it.supportDamageBonusByLevel.map(x => String(x ?? '').trim())
        : []
      const byTier = Array.isArray(it.supportDamageBonusByTier)
        ? it.supportDamageBonusByTier.map(x => String(x ?? '').trim())
        : []
      const prev = m.get(id) ?? { byLevel: null, byTier: null }
      if (byLevel.length) prev.byLevel = byLevel
      if (byTier.length === 3) prev.byTier = byTier
      m.set(id, prev)
    }
  }
  merge(supportSkillTagsData.supportSkills as { id?: unknown; supportDamageBonusByLevel?: unknown; supportDamageBonusByTier?: unknown }[])
  merge(nobleSupportSkillTagsData.supportSkills as { id?: unknown; supportDamageBonusByLevel?: unknown; supportDamageBonusByTier?: unknown }[])
  merge(
    magnificentSupportSkillTagsData.supportSkills as {
      id?: unknown
      supportDamageBonusByLevel?: unknown
      supportDamageBonusByTier?: unknown
    }[]
  )
  return m
})()

/** 与 SkillLinkCard 一致：wiki 专属辅助 slug 含 (Noble)/(Magnificent) */
function isWikiExclusiveSupportSkillId(skillId: string): boolean {
  const id = skillId.trim()
  if (!id) return false
  const u = id.toLowerCase()
  if (u.includes('%28noble%29') || u.includes('%28magnificent%29')) return true
  try {
    const dec = decodeURIComponent(id).toLowerCase()
    return dec.includes('(noble)') || dec.includes('(magnificent)')
  } catch {
    return false
  }
}

/** 崇高/华贵槽自定义：纯数字视为百分比；否则解析首个 x% */
function parseSupportExclusiveCustomPercent(raw: string): number | null {
  const t = String(raw ?? '').trim()
  if (!t) return null
  if (/^\d+(\.\d+)?$/.test(t)) {
    const v = Number(t)
    return Number.isFinite(v) ? v : null
  }
  return parseFirstPercentValue(t)
}

function resolveSupportDamagePercentFromMeta(id: string, lvRaw: number): number | null {
  const idTrim = String(id ?? '').trim()
  if (!idTrim) return null
  const meta = supportDmgMetaById.get(idTrim)
  if (!meta) return null
  const wikiExclusive = isWikiExclusiveSupportSkillId(idTrim)
  const tiers = meta.byTier
  if (wikiExclusive || tiers?.length === 3) {
    if (!tiers?.length) return null
    const lv = Math.min(Math.max(Math.round(lvRaw), 1), 3)
    const s = (tiers[lv - 1] ?? '').trim()
    if (!s) return null
    return parseFirstPercentValue(s.includes('%') ? s : `${s}%`)
  }
  const arr = meta.byLevel
  if (!arr?.length) return null
  const lv = Math.max(1, Math.floor(lvRaw))
  if (lv < 1 || lv > arr.length) return null
  const s = (arr[lv - 1] ?? '').trim()
  return parseFirstPercentValue(`${s}%`)
}

const auraSupportSkillIdSet = (() => {
  const s = new Set<string>()
  const add = (
    arr:
      | {
          id?: unknown
          tags?: unknown
        }[]
      | undefined
  ) => {
    for (const it of arr ?? []) {
      const id = String(it.id ?? '').trim()
      if (!id) continue
      const tags = Array.isArray(it.tags) ? it.tags.map(x => String(x ?? '').trim()) : []
      if (tags.includes('光环')) s.add(id)
    }
  }
  add(supportSkillTagsData.supportSkills as { id?: unknown; tags?: unknown }[])
  add(nobleSupportSkillTagsData.supportSkills as { id?: unknown; tags?: unknown }[])
  add(magnificentSupportSkillTagsData.supportSkills as { id?: unknown; tags?: unknown }[])
  return s
})()
const PRECISE_STAND_AS_ONE_ID = 'Precise%3A_Stand_as_One'

const passiveParsedBonusById = (() => {
  const m = new Map<
    string,
    Array<{
      level: number
      description?: string
      damageExtraPct?: number
      critValuePct?: number
      attackSpeedPct?: number
      castSpeedPct?: number
    }>
  >()
  const list =
    (passiveSkillTagsData as {
      passiveSkills?: Array<{ id?: unknown; parsedBonusesByLevel?: unknown }>
    }).passiveSkills ?? []
  for (const it of list) {
    const id = String(it.id ?? '').trim()
    if (!id) continue
    const rowsRaw = it.parsedBonusesByLevel
    if (!Array.isArray(rowsRaw)) continue
    const rows = rowsRaw
      .map(r => {
        if (!r || typeof r !== 'object') return null
        const o = r as Record<string, unknown>
        const level = Number(o.level)
        if (!Number.isFinite(level)) return null
        const description = String(o.description ?? '')
        const dmg =
          typeof o.damageExtraPct === 'number' && Number.isFinite(o.damageExtraPct)
            ? o.damageExtraPct
            : undefined
        const crit =
          typeof o.critValuePct === 'number' && Number.isFinite(o.critValuePct)
            ? o.critValuePct
            : undefined
        const aspd =
          typeof o.attackSpeedPct === 'number' && Number.isFinite(o.attackSpeedPct)
            ? o.attackSpeedPct
            : undefined
        const cspd =
          typeof o.castSpeedPct === 'number' && Number.isFinite(o.castSpeedPct)
            ? o.castSpeedPct
            : undefined
        return {
          level,
          description,
          damageExtraPct: dmg,
          critValuePct: crit,
          attackSpeedPct: aspd,
          castSpeedPct: cspd
        }
      })
      .filter(Boolean) as Array<{
      level: number
      description?: string
      damageExtraPct?: number
      critValuePct?: number
      attackSpeedPct?: number
      castSpeedPct?: number
    }>
    if (rows.length) m.set(id, rows)
  }
  return m
})()

/**
 * 已选职业面板（非神格盘）的 tags 含「魔灵」或「召唤」时，天赋/追忆里含召唤物/魔灵/智械子句仍可参与 **攻速、施法速度 inc** 解析。
 * 全局 **伤害提高（inc）** 口径见 effectClauseSkipForPlayerGlobalDamageInc：召唤侧与承伤转移类一律不计入玩家伤害池。
 */
const dmgIncludeSummonMinionStatLines = computed(() => {
  for (const t of professionTalentStore.trees) {
    if (!t.isSelected || t.isGodRoot) continue
    for (const tag of t.tags ?? []) {
      const x = String(tag ?? '').trim()
      if (x === '魔灵' || x === '召唤') return true
    }
  }
  return false
})

/** 天赋/追忆子句过滤（攻速/施法 inc）：召唤物·魔灵·智械受职业 tag 控制；哨卫/哨位仅核心为哨卫技能时计入 */
type PlayerDmgEffectLineCtx = {
  allowSummonMinionKeywords: boolean
  coreSkillIsSentry: boolean
}

function effectClauseHasMinionProfessionKeywords(clause: string): boolean {
  const s = String(clause ?? '')
  return s.includes('召唤物') || s.includes('魔灵') || s.includes('智械')
}

function effectClauseHasSentryKeywords(clause: string): boolean {
  const s = String(clause ?? '')
  return s.includes('哨卫') || s.includes('哨位')
}

/** 承伤/伤害转嫁给召唤物等，邻域含「伤害」易误判为伤害 inc，整子句排除 */
function effectClauseIsDamageRedirectTransfer(clause: string): boolean {
  const s = String(clause ?? '')
  return s.includes('转移至') || s.includes('伤害转移')
}

/**
 * 全局「玩家伤害 inc」子句排除：召唤物/魔灵/智械、非哨卫核心时的哨卫文案、承伤转移类。
 * 与 effectClauseSkipForPlayerDmgPool 区分：后者仅用于攻速/施法，且召唤侧仍看职业 tag。
 * `ctx` 省略时：仍排除转移与召唤侧；哨卫关键词保守视为跳过（等同 core 非哨卫）。
 */
function effectClauseSkipForPlayerGlobalDamageInc(
  clause: string,
  ctx?: PlayerDmgEffectLineCtx
): boolean {
  if (effectClauseIsDamageRedirectTransfer(clause)) return true
  if (effectClauseHasMinionProfessionKeywords(clause)) return true
  const sentryOk = ctx?.coreSkillIsSentry ?? false
  if (!sentryOk && effectClauseHasSentryKeywords(clause)) return true
  return false
}

function effectClauseSkipForPlayerDmgPool(clause: string, ctx: PlayerDmgEffectLineCtx): boolean {
  if (!ctx.allowSummonMinionKeywords && effectClauseHasMinionProfessionKeywords(clause)) return true
  if (!ctx.coreSkillIsSentry && effectClauseHasSentryKeywords(clause)) return true
  return false
}

/** 计入玩家全局伤害 inc / 持续 inc 的子句（已排除召唤物/魔灵/智械、转嫁、非哨卫时的哨卫文等） */
function filterPartsForPlayerGlobalDamageInc(
  line: string,
  ctx?: PlayerDmgEffectLineCtx
): string[] {
  return splitLineIntoEffectClauses(line).filter(
    p => !p.includes('转化为') && !effectClauseSkipForPlayerGlobalDamageInc(p, ctx)
  )
}

/** 被动描述整行：召唤侧、哨卫条件、承伤转移与攻速/施法子句策略对齐 */
function effectTextBlocksPassiveRowForPlayer(desc: string, ctx: PlayerDmgEffectLineCtx): boolean {
  const d = String(desc ?? '')
  if (effectClauseIsDamageRedirectTransfer(d)) return true
  if (effectClauseHasMinionProfessionKeywords(d)) return true
  if (!ctx.coreSkillIsSentry && effectClauseHasSentryKeywords(d)) return true
  return false
}

const supportMorePctFromAllLinks = computed(() => {
  return skillDerivedSummary.value.damageMorePctList
})

const skillDerivedSummary = computed(() => {
  const s = previewSkills.value as Record<string, unknown>
  const playerDmgCtx: PlayerDmgEffectLineCtx = {
    allowSummonMinionKeywords: dmgIncludeSummonMinionStatLines.value,
    coreSkillIsSentry: coreSkillIsSentryType(s)
  }
  const coreLink = normalizeSkillLink(s.core)
  const activeLinks = Array.isArray(s.active) ? s.active.map(normalizeSkillLink) : []
  const passiveLinks = Array.isArray(s.passive) ? s.passive.map(normalizeSkillLink) : []
  const normalLinks = [
    coreLink,
    ...activeLinks
  ]
  const out: number[] = []
  const damageMoreSources: { pct: number; label: string }[] = []
  for (const link of normalLinks) {
    const ids = link.supportSkillIds ?? []
    const lvs = link.supportSkillLevels ?? []
    const customs = link.supportExclusiveCustomBonuses ?? []
    const auraSupportCount = ids.reduce((sum, sid) => {
      const id = String(sid ?? '').trim()
      if (!id) return sum
      return sum + (auraSupportSkillIdSet.has(id) ? 1 : 0)
    }, 0)
    for (let i = 0; i < ids.length; i++) {
      const id = String(ids[i] ?? '').trim()
      if (!id) continue
      const auraMultiplier = id === PRECISE_STAND_AS_ONE_ID ? Math.max(1, auraSupportCount) : 1
      const supportName = skillIdToName.get(id) ?? id
      const customPct = parseSupportExclusiveCustomPercent(customs[i] ?? '')
      if (customPct != null) {
        const p = customPct * auraMultiplier
        out.push(p)
        damageMoreSources.push({
          pct: p,
          label:
            auraMultiplier > 1
              ? `${supportName}（自定义 ${customPct}%×${auraMultiplier}）`
              : `${supportName}（自定义 ${customPct}%）`
        })
        continue
      }
      const lv = Number.isFinite(lvs[i] as number) ? Math.max(1, Math.floor(lvs[i]!)) : 20
      const pct = resolveSupportDamagePercentFromMeta(id, lv)
      if (pct != null) {
        const p = pct * auraMultiplier
        out.push(p)
        damageMoreSources.push({
          pct: p,
          label:
            auraMultiplier > 1
              ? `${supportName} Lv.${lv}（×${auraMultiplier}）`
              : `${supportName} Lv.${lv}`
        })
      }
    }
  }

  // 被动链路：主被动 + 其辅助按乘算合并为单条 more
  for (const link of passiveLinks) {
    let mult = 1
    let hasAny = false
    const mainId = String(link.mainSkillId ?? '').trim()
    const mainLv = Number.isFinite(link.mainSkillLevel as number)
      ? Math.max(1, Math.floor(link.mainSkillLevel!))
      : 20
    if (mainId) {
      const rows = passiveParsedBonusById.get(mainId)
      const row = rows?.find(r => r.level === mainLv)
      const desc = String(row?.description ?? '')
      const skipPassiveDmgRow = effectTextBlocksPassiveRowForPlayer(desc, playerDmgCtx)
      let mainPct: number | null = null
      if (!skipPassiveDmgRow) {
        mainPct =
          typeof row?.damageExtraPct === 'number' && Number.isFinite(row.damageExtraPct)
            ? row.damageExtraPct
            : parsePercentByKeywords(
                row?.description,
                ['伤害', '持续伤害', '攻击伤害', '法术伤害', '元素伤害'],
                ['暴击伤害']
              )
      }
      if (mainPct != null) {
        mult *= 1 + mainPct / 100
        hasAny = true
      }
    }

    const ids = link.supportSkillIds ?? []
    const lvs = link.supportSkillLevels ?? []
    const customs = link.supportExclusiveCustomBonuses ?? []
    const auraSupportCount = ids.reduce((sum, sid) => {
      const id = String(sid ?? '').trim()
      if (!id) return sum
      return sum + (auraSupportSkillIdSet.has(id) ? 1 : 0)
    }, 0)
    for (let i = 0; i < ids.length; i++) {
      const id = String(ids[i] ?? '').trim()
      if (!id) continue
      const auraMultiplier = id === PRECISE_STAND_AS_ONE_ID ? Math.max(1, auraSupportCount) : 1
      const customPct = parseSupportExclusiveCustomPercent(customs[i] ?? '')
      if (customPct != null) {
        mult *= 1 + (customPct * auraMultiplier) / 100
        hasAny = true
        continue
      }
      const lv = Number.isFinite(lvs[i] as number) ? Math.max(1, Math.floor(lvs[i]!)) : 20
      const pct = resolveSupportDamagePercentFromMeta(id, lv)
      if (pct != null) {
        mult *= 1 + (pct * auraMultiplier) / 100
        hasAny = true
      }
    }
    if (hasAny) {
      const p = (mult - 1) * 100
      out.push(p)
      const mainName = mainId ? skillIdToName.get(mainId) ?? mainId : '被动'
      damageMoreSources.push({
        pct: p,
        label: `被动链路合并 · ${mainName} Lv.${mainLv}`
      })
    }
  }
  let passiveCritPctAttack = 0
  let passiveCritPctSpell = 0
  let passiveCritFlatAttack = 0
  let passiveCritFlatSpell = 0
  const passiveCritRows: Array<{ label: string; contributions: CritContribution[] }> = []

  function mergePassiveCritContributions(contributions: CritContribution[]) {
    for (const c of contributions) {
      if (c.kind === 'pct') {
        if (c.scope === 'attack') passiveCritPctAttack += c.value
        else if (c.scope === 'spell') passiveCritPctSpell += c.value
        else {
          passiveCritPctAttack += c.value
          passiveCritPctSpell += c.value
        }
      } else {
        if (c.scope === 'attack') passiveCritFlatAttack += c.value
        else if (c.scope === 'spell') passiveCritFlatSpell += c.value
        else {
          passiveCritFlatAttack += c.value
          passiveCritFlatSpell += c.value
        }
      }
    }
  }

  let attackSpeedIncPct = 0
  let castSpeedIncPct = 0
  let passiveCritDamageIncPct = 0
  const passiveCritDamageRows: { label: string; pct: number }[] = []

  for (const link of passiveLinks) {
    const mainId = String(link.mainSkillId ?? '').trim()
    const mainLv = Number.isFinite(link.mainSkillLevel as number)
      ? Math.max(1, Math.floor(link.mainSkillLevel!))
      : 20
    if (!mainId) continue
    const rows = passiveParsedBonusById.get(mainId)
    const row = rows?.find(r => r.level === mainLv)
    const desc2 = String(row?.description ?? '')
    const skipRow2 = effectTextBlocksPassiveRowForPlayer(desc2, playerDmgCtx)
    let attackPct: number | null = null
    let castPct: number | null = null
    const critContribs: CritContribution[] = []
    if (!skipRow2) {
      if (typeof row?.critValuePct === 'number' && Number.isFinite(row.critValuePct)) {
        critContribs.push({ kind: 'pct', value: row.critValuePct, scope: 'both' })
      } else {
        critContribs.push(...parseCritContributionsFromEffectLine(desc2))
      }
      attackPct =
        typeof row?.attackSpeedPct === 'number' && Number.isFinite(row.attackSpeedPct)
          ? row.attackSpeedPct
          : parsePercentByKeywords(row?.description, ['攻击速度', '攻速'])
      castPct =
        typeof row?.castSpeedPct === 'number' && Number.isFinite(row.castSpeedPct)
          ? row.castSpeedPct
          : parsePercentByKeywords(row?.description, ['施法速度', '施法'])
      const critDmgVals = extractCritDamageIncPctValuesFromLine(desc2, {
        playerDmgCtx,
        primaryStats: buildPrimaryStatsForAnnotation.value,
        skillKind: dmgSkillKind.value
      })
      const critDmgSum = critDmgVals.reduce((a, b) => a + b, 0)
      if (critDmgSum !== 0) {
        passiveCritDamageIncPct += critDmgSum
        passiveCritDamageRows.push({
          label: `被动 · ${skillIdToName.get(mainId) ?? mainId} Lv.${mainLv}`,
          pct: critDmgSum
        })
      }
    }
    if (critContribs.length) {
      mergePassiveCritContributions(critContribs)
      passiveCritRows.push({
        label: `被动 · ${skillIdToName.get(mainId) ?? mainId} Lv.${mainLv}`,
        contributions: critContribs
      })
    }
    if (attackPct != null) attackSpeedIncPct += attackPct
    if (castPct != null) castSpeedIncPct += castPct
  }

  return {
    damageMorePctList: out,
    damageMoreSources,
    passiveCritPctAttack,
    passiveCritPctSpell,
    passiveCritFlatAttack,
    passiveCritFlatSpell,
    passiveCritRows,
    passiveCritDamageIncPct,
    passiveCritDamageRows,
    attackSpeedIncPct,
    castSpeedIncPct
  }
})

function critScopeAppliesToSkill(
  scope: CritValueScope | undefined,
  skillKind: 'attack' | 'spell'
): boolean {
  const sc = scope ?? 'both'
  if (sc === 'both') return true
  return sc === skillKind
}

function sumCritContributionsForKind(
  contributions: CritContribution[],
  skillKind: 'attack' | 'spell',
  which: 'pct' | 'flat'
): number {
  let s = 0
  const atk = skillKind === 'attack'
  for (const c of contributions) {
    if (c.kind !== which) continue
    if (c.scope === 'both') s += c.value
    else if (atk && c.scope === 'attack') s += c.value
    else if (!atk && c.scope === 'spell') s += c.value
  }
  return s
}

function truncateCritEffectLabel(line: string, maxLen = 88): string {
  const t = line.replace(/\s+/g, ' ').trim()
  if (t.length <= maxLen) return t
  return `${t.slice(0, maxLen)}…`
}

function stripHtmlLikeText(s: string): string {
  return s.replace(/<[^>]*>/g, '').replace(/\s+/g, ' ').trim()
}

function extractPctValuesByKeyword(text: string, keyword: string): number[] {
  const out: number[] = []
  const re = new RegExp(`([+-]?\\d+(?:\\.\\d+)?)\\s*%\\s*${keyword}`, 'g')
  let m: RegExpExecArray | null = null
  while ((m = re.exec(text)) != null) {
    const n = Number(m[1])
    if (Number.isFinite(n)) out.push(n)
  }
  return out
}

type ExtractPctByKeywordsOpts = {
  /**
   * 若本段 % 前后窗口内出现该子串，则跳过该次匹配（不并入 inc）。
   * 伤害 inc 用「额外」：游戏中「额外 X% … 伤害」多为 more/独立乘区，非提高类 inc。
   */
  skipMatchIfAroundIncludes?: string
  /** 邻域内出现任一则跳过（击中类 inc 用于排除「持续伤害」「异常伤害」等专用池） */
  skipAroundIncludesAny?: string[]
  /** 邻域内须含此子串才计入（持续伤害 inc 专用） */
  requireAroundIncludes?: string
  /** 向前取字符数，用于关键词匹配与 skip 检测（默认 16） */
  windowBefore?: number
  /** 向后取字符数（默认 16） */
  windowAfter?: number
}

/** 天赋合并展示用「 xN」后缀，子句切分前剥掉 */
function stripTalentEffectRepeatCountSuffix(line: string): string {
  return String(line ?? '')
    .replace(/\s+x\d+$/i, '')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * 将一行效果拆成子句，供伤害/攻速/施法 inc 与 playerDmgCtx 过滤（召唤物、哨卫等）。
 * 覆盖：标点、并列连词、无标点连续「…%+…%」。
 */
function splitLineIntoEffectClauses(line: string): string[] {
  const t = stripTalentEffectRepeatCountSuffix(line)
  if (!t) return []

  let parts = t
    .split(/[，,、；;｜|\n\r／·]+/)
    .map(p => p.trim())
    .filter(Boolean)
  if (parts.length === 0) parts = [t]

  const withConj: string[] = []
  for (const p of parts) {
    withConj.push(...p.split(/\s+(?:和|与|及|以及)\s+/).map(x => x.trim()).filter(Boolean))
  }
  if (withConj.length) parts = withConj

  const final: string[] = []
  for (const p of parts) {
    const sub = p.split(/(?<=%)\s*(?=[+＋])/).map(x => x.trim()).filter(Boolean)
    final.push(...(sub.length > 1 ? sub : [p]))
  }
  return final.length ? final : [t]
}

type PrimaryStatsForScaling = { 力量: number; 敏捷: number; 智慧: number }

/** `+12每点力量` → `每12点力量`，便于与「每 N 点…+X%」连读 */
function normalizeEveryNPrimarySyntax(t: string): string {
  return t.replace(/([+＋]?\d+(?:\.\d+)?)每点(力量|敏捷|智慧)/g, (_, rawNum: string, attr: string) => {
    const n = rawNum.replace(/^[+＋]/, '')
    return `每${n}点${attr}`
  })
}

function tryConsumeSkipBonus(bag: Map<number, number> | undefined, n: number): boolean {
  if (!bag) return false
  const c = bag.get(n) ?? 0
  if (c <= 0) return false
  bag.set(n, c - 1)
  return true
}

/** 在已去空白字符串上提取 %；`skipPctIndexRanges` 内起始的 % 匹配不计入（避免与「X%每点力量」重复） */
function extractPctValuesByKeywordsOnCompact(
  t: string,
  keywords: string[],
  opts: ExtractPctByKeywordsOpts | undefined,
  skipPctIndexRanges: { start: number; end: number }[],
  skipPlainPctBonuses?: Map<number, number>
): number[] {
  const out: number[] = []
  if (!t || keywords.length === 0) return out
  const wb = opts?.windowBefore ?? 16
  const wa = opts?.windowAfter ?? 16
  const re = /([+-]?\d+(?:\.\d+)?)%/g
  let m: RegExpExecArray | null = null
  while ((m = re.exec(t)) != null) {
    const idx = m.index
    if (skipPctIndexRanges.some(r => idx >= r.start && idx < r.end)) continue
    const n = Number(m[1])
    if (!Number.isFinite(n)) continue
    const around = t.slice(Math.max(0, idx - wb), Math.min(t.length, idx + m[0].length + wa))
    if (opts?.skipMatchIfAroundIncludes && around.includes(opts.skipMatchIfAroundIncludes)) {
      continue
    }
    if (opts?.skipAroundIncludesAny?.some(s => around.includes(s))) {
      continue
    }
    if (opts?.requireAroundIncludes && !around.includes(opts.requireAroundIncludes)) {
      continue
    }
    if (keywords.some(k => around.includes(k))) {
      if (tryConsumeSkipBonus(skipPlainPctBonuses, n)) continue
      out.push(n)
    }
  }
  return out
}

/**
 * 子句内 `X%每N点属性` / `X%每点属性`：按 **X% × (属性 / N)** 计入（每点 = N=1）；区间用于排除字面 % 的重复提取。
 */
function perPointPrimaryPctScaledSegments(
  t: string,
  prim: PrimaryStatsForScaling,
  qualifyAround: (around: string) => boolean
): { start: number; end: number; scaledPct: number }[] {
  const segments: { start: number; end: number; scaledPct: number }[] = []
  const wb = 40
  const wa = 20

  const rePPN = /([+＋]?\d+(?:\.\d+)?)%每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)/g
  let m: RegExpExecArray | null
  while ((m = rePPN.exec(t)) !== null) {
    const bonus = parseFloat(m[1]!.replace(/^[+＋]/, ''))
    const interval = parseFloat(m[2]!)
    const attr = m[3] as keyof PrimaryStatsForScaling
    if (!Number.isFinite(bonus) || !Number.isFinite(interval) || interval <= 0) continue
    const idx = m.index
    const around = t.slice(Math.max(0, idx - wb), Math.min(t.length, idx + m[0].length + wa))
    if (!qualifyAround(around)) continue
    const st = prim[attr]
    const s = Number.isFinite(st) ? st : 0
    segments.push({ start: idx, end: idx + m[0].length, scaledPct: (bonus * s) / interval })
  }

  const rePP1 = /([+＋]?\d+(?:\.\d+)?)%每点(力量|敏捷|智慧)/g
  while ((m = rePP1.exec(t)) !== null) {
    const bonus = parseFloat(m[1]!.replace(/^[+＋]/, ''))
    if (!Number.isFinite(bonus)) continue
    const attr = (m[0].match(/每点(力量|敏捷|智慧)$/) ?? [])[1] as keyof PrimaryStatsForScaling | undefined
    if (!attr) continue
    const idx = m.index
    const around = t.slice(Math.max(0, idx - wb), Math.min(t.length, idx + m[0].length + wa))
    if (!qualifyAround(around)) continue
    const st = prim[attr]
    const s = Number.isFinite(st) ? st : 0
    segments.push({ start: idx, end: idx + m[0].length, scaledPct: bonus * s })
  }

  const segOverlaps = (start: number, end: number) =>
    segments.some(s => start < s.end && end > s.start)
  const reRev = /([+＋]?\d+(?:\.\d+)?)%[^每]{0,80}?每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)/g
  while ((m = reRev.exec(t)) !== null) {
    const bonus = parseFloat(m[1]!.replace(/^[+＋]/, ''))
    const interval = parseFloat(m[2]!)
    const attr = m[3] as keyof PrimaryStatsForScaling
    if (!Number.isFinite(bonus) || !Number.isFinite(interval) || interval <= 0) continue
    const idx = m.index
    const end = idx + m[0].length
    if (segOverlaps(idx, end)) continue
    const around = t.slice(Math.max(0, idx - wb), Math.min(t.length, end + wa))
    if (!qualifyAround(around)) continue
    const st = prim[attr]
    const s = Number.isFinite(st) ? st : 0
    segments.push({ start: idx, end, scaledPct: (bonus * s) / interval })
  }
  return segments
}

/** 攻速 / 施法 inc；有 primaryStats 时 `X%每N点属性` 按 **X×属性/N**（每点 N=1） */
function extractSpeedIncPctValuesFromLine(
  line: string,
  keywords: string[],
  playerDmgCtx: PlayerDmgEffectLineCtx | undefined,
  prim?: PrimaryStatsForScaling
): number[] {
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const out: number[] = []
  for (const part of parts) {
    if (playerDmgCtx && effectClauseSkipForPlayerDmgPool(part, playerDmgCtx)) continue
    if (!prim) {
      out.push(...extractPctValuesByKeywords(part, keywords, undefined))
      continue
    }
    const t = part.replace(/\s+/g, '')
    const segs = perPointPrimaryPctScaledSegments(t, prim, around =>
      keywords.some(k => around.includes(k))
    )
    const ranges = segs.map(s => ({ start: s.start, end: s.end }))
    out.push(...extractPctValuesByKeywordsOnCompact(t, keywords, undefined, ranges))
    for (const s of segs) out.push(s.scaledPct)
  }
  return out
}

/**
 * 从一行效果里取伤害 inc 用的百分数：按子句切分后，**含「转化为」的子句整段跳过**（转伤归独立模块，不计入提高池）。
 * 玩家全局 inc：召唤物/魔灵/智械子句一律跳过；非哨卫核心时跳过「哨卫/哨位」；「转移至」等承伤转嫁类跳过。
 * 有 primaryStats 时：按 **每 N 点属性** 间隔用除法 — `加成% × (粗算属性 / N)`；`每点` 等价 N=1。
 * 「每12点力量，+1%火」或「+12每点力量，+1%火」（归一化后）在同一玩家池行内配对时，字面 `+1%` 不再重复计入。
 */
function extractDamageIncPctValuesFromLine(
  line: string,
  opts?: { playerDmgCtx?: PlayerDmgEffectLineCtx; primaryStats?: PrimaryStatsForScaling }
): number[] {
  const ctx = opts?.playerDmgCtx
  const prim = opts?.primaryStats
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const kwOpts: ExtractPctByKeywordsOpts = {
    skipMatchIfAroundIncludes: '额外',
    skipAroundIncludesAny: ['持续伤害', '异常伤害', '暴击伤害'],
    windowBefore: 40,
    windowAfter: 20
  }
  const dmgKeywords = ['伤害', '增伤', '伤害提高', '攻击伤害', '法术伤害', '元素伤害']
  /** 仅用「玩家池」子句判断：避免整行里召唤物子句含「伤害」导致其它子句的每点属性被误计 */
  const playerPartsOnly = filterPartsForPlayerGlobalDamageInc(line, ctx)
  const lineHasPlayerDmgKw = dmgKeywords.some(kw =>
    playerPartsOnly.some(p => p.replace(/\s+/g, '').includes(kw))
  )

  const out: number[] = []
  const skipPlainBonuses = prim ? new Map<number, number>() : undefined

  if (prim && skipPlainBonuses) {
    const joinedNorm = normalizeEveryNPrimarySyntax(
      playerPartsOnly.map(p => p.replace(/\s+/g, '')).join('')
    )
    const rePair = /每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)[^%]{0,80}?([+＋]?\d+(?:\.\d+)?)%/g
    let pm: RegExpExecArray | null
    while ((pm = rePair.exec(joinedNorm)) !== null) {
      const interval = parseFloat(pm[1]!)
      const attr = pm[2] as keyof PrimaryStatsForScaling
      const bonus = parseFloat(pm[3]!.replace(/^[+＋]/, ''))
      if (!Number.isFinite(interval) || interval <= 0 || !Number.isFinite(bonus)) continue
      const frag = pm[0]!
      const ok =
        !frag.includes('暴击伤害') &&
        (dmgKeywords.some(k => frag.includes(k)) || lineHasPlayerDmgKw)
      if (!ok) continue
      const st = prim[attr]
      if (!Number.isFinite(st)) continue
      out.push((bonus * st) / interval)
      skipPlainBonuses.set(bonus, (skipPlainBonuses.get(bonus) ?? 0) + 1)
    }
  }

  for (const part of parts) {
    if (part.includes('转化为')) continue
    if (effectClauseSkipForPlayerGlobalDamageInc(part, ctx)) continue
    const t = part.replace(/\s+/g, '')
    if (prim) {
      const segs = perPointPrimaryPctScaledSegments(t, prim, around => {
        if (around.includes('额外')) return false
        if (['持续伤害', '异常伤害'].some(s => around.includes(s))) return false
        if (around.includes('暴击伤害')) return false
        return dmgKeywords.some(k => around.includes(k))
      })
      const ranges = segs.map(s => ({ start: s.start, end: s.end }))
      out.push(
        ...extractPctValuesByKeywordsOnCompact(t, dmgKeywords, kwOpts, ranges, skipPlainBonuses)
      )
      for (const s of segs) out.push(s.scaledPct)
    } else {
      out.push(...extractPctValuesByKeywords(part, dmgKeywords, kwOpts))
    }
  }
  return out
}

function damageMorePartAppliesToSkill(part: string, kind: SkillBaseDamageKind): boolean {
  const t = part.replace(/\s+/g, '')
  if (t.includes('法术伤害')) return kind === 'spell'
  if (t.includes('攻击伤害')) return kind === 'attack'
  return true
}

/**
 * 承伤/受击类「额外 … 伤害」文案，不计入击中 more。
 * 注意：「受到的物理伤害」不含连续子串「受到的伤害」，需单独用「受到的…伤害」匹配；
 * 「来自近处敌人的伤害」等为受击来源描述，亦排除。
 */
function hitDamageMoreTextIsIncomingDamageTaken(text: string): boolean {
  const t = text.replace(/\s+/g, '')
  if (t.includes('受到的伤害') || t.includes('承受的伤害')) return true
  if (/受到的[^，。；%]{0,20}伤害/.test(t)) return true
  if (/来自[^，。；]{0,32}敌人[^，。；]{0,16}伤害/.test(t)) return true
  return false
}

/** 无词缀时各祝福类层数上限的演示默认值（与常见「初始上限为 4 层」一致） */
const DEFAULT_BLESSING_BASE_CAP = 4

/** 摘要区展示用（层数仍对任意 X 从装备+天赋按「X层数上限」解析） */
const COMMON_BLESSING_NAMES_FOR_UI = ['坚韧祝福', '聚能祝福', '灵动祝福'] as const

function escapeRegExp(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}

function compactZhLine(line: string): string {
  return normDashChars(line).replace(/\s+/g, '')
}

function normDashChars(s: string): string {
  return s.replace(/[–−—]/g, '-')
}

/**
 * 单条效果文案中，对「{name}层数上限」的代数增量（含 +N / -N / 区间）。
 */
function sumBlessingCapDeltaFromLine(line: string, blessingName: string): number {
  const name = blessingName.trim()
  if (!name) return 0
  const t = compactZhLine(line).replace(/[＋]/g, '+')
  const esc = escapeRegExp(name)
  let sum = 0
  let m: RegExpExecArray | null
  const reRange = new RegExp(
    `\\(([-+]?\\d+(?:\\.\\d+)?)-([-+]?\\d+(?:\\.\\d+)?)\\)${esc}层数上限`,
    'g'
  )
  while ((m = reRange.exec(t)) !== null) {
    const a = parseFloat(m[1]!)
    const b = parseFloat(m[2]!)
    if (Number.isFinite(a) && Number.isFinite(b)) sum += (a + b) / 2
  }
  const reFlat = new RegExp(`([+-]?\\d+(?:\\.\\d+)?)${esc}层数上限`, 'g')
  while ((m = reFlat.exec(t)) !== null) {
    const n = parseFloat(m[1]!)
    if (Number.isFinite(n)) sum += n
  }
  return sum
}

function sumExtraOwnedBlessingStacksFromLine(line: string, blessingName: string): number {
  const name = blessingName.trim()
  if (!name) return 0
  const t = compactZhLine(line)
  const esc = escapeRegExp(name)
  const re = new RegExp(`额外拥有(\\d+)(?:层|層)${esc}`, 'g')
  let sum = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(t)) !== null) {
    const n = parseInt(m[1]!, 10)
    if (Number.isFinite(n)) sum += n
  }
  return sum
}

function estimateBlessingStacksFromBuild(blessingName: string): number {
  const name = blessingName.trim()
  if (!name) return 0
  const eq = buildStore.snapshot.equipment as Record<string, unknown>
  const equipped = Array.isArray(eq?.equipped) ? eq.equipped : []
  let delta = 0
  let extraOwned = 0
  for (let i = 0; i < equipped.length; i++) {
    if (equipped[i] == null) continue
    for (const raw of getResolvedEffectLinesForEquipmentSlot(eq, i)) {
      const line = stripHtmlLikeText(String(raw ?? ''))
      if (!line) continue
      delta += sumBlessingCapDeltaFromLine(line, name)
      extraOwned += sumExtraOwnedBlessingStacksFromLine(line, name)
    }
  }
  for (const x of professionTalentStore.getAllocatedEffects()) {
    const line = stripHtmlLikeText(String(x ?? ''))
    if (!line) continue
    delta += sumBlessingCapDeltaFromLine(line, name)
    extraOwned += sumExtraOwnedBlessingStacksFromLine(line, name)
  }
  return Math.max(0, Math.floor(DEFAULT_BLESSING_BASE_CAP + delta + extraOwned))
}

/**
 * 从「X」起往后解析按层 more 的百分数：支持 `+14%`、`+(14–15)%`、`额外 +14 %` 等；区间取中值。
 * `subjectCompact` 为已去空白的增益名称（与 compact 行一致）。
 */
function parseBlessingMorePctFromSubjectTail(tail: string, subjectCompact: string): number | null {
  const u = normDashChars(tail)
    .replace(/[＋]/g, '+')
    .replace(/％/g, '%')
    .replace(/\s+/g, '')
  const tryPair = (a: string, b: string): number | null => {
    const x = parseFloat(a)
    const y = parseFloat(b)
    if (!Number.isFinite(x) || !Number.isFinite(y)) return null
    return (x + y) / 2
  }
  let m = u.match(/额外\+?\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\)%/)
  if (m) {
    const mid = tryPair(m[1]!, m[2]!)
    if (mid != null) return mid
  }
  m = u.match(/额外\+?(\d+(?:\.\d+)?)%/)
  if (m) {
    const x = parseFloat(m[1]!)
    if (Number.isFinite(x)) return x
  }
  m = u.match(/[,，]?\+?\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\)%/)
  if (m) {
    const mid = tryPair(m[1]!, m[2]!)
    if (mid != null) return mid
  }
  m = u.match(/[,，]?\+(\d+(?:\.\d+)?)%/)
  if (m) {
    const x = parseFloat(m[1]!)
    if (Number.isFinite(x)) return x
  }
  // tail 已从 X 起截断，避免把 X 拼进 RegExp 源（易因转义产生 Invalid / Unterminated）
  const sub = subjectCompact
  let rest = u.startsWith(sub) ? u.slice(sub.length) : u
  if (rest === u && sub.length) {
    const ix = u.indexOf(sub)
    if (ix >= 0) rest = u.slice(ix + sub.length)
  }
  m = rest.match(/^[^%]{0,80}?[+]\((\d+(?:\.\d+)?)-(\d+(?:\.\d+)?)\)%/)
  if (m) {
    const mid = tryPair(m[1]!, m[2]!)
    if (mid != null) return mid
  }
  m = rest.match(/^[^%]{0,80}?[+](\d+(?:\.\d+)?)%/)
  if (m) {
    const x = parseFloat(m[1]!)
    if (Number.isFinite(x)) return x
  }
  return null
}

const RE_PER_LAYER_SUBJECT = /每(?:有)?(\d+)(?:层|層)([^，,；。%+]{2,40}?)(?=，|,|额外|[+＋(]|$)/

/**
 * 「每有 N 层 X … +Y%伤害」类：解析 X 与每层等价 more%（Y/N）。
 */
function parsePerLayerSubjectScaledMore(line: string): {
  perN: number
  subject: string
  perStackEquiv: number
} | null {
  const t = compactZhLine(line).replace(/[＋]/g, '+')
  let perN = 0
  let subject = ''
  let tailFromSubject = ''
  const m1 = RE_PER_LAYER_SUBJECT.exec(t)
  if (m1) {
    perN = parseInt(m1[1]!, 10)
    subject = m1[2]!
    const subStart = m1.index + m1[0].length - subject.length
    tailFromSubject = subStart >= 0 ? t.slice(subStart) : t
  } else {
    const re2 = /每一(?:层|層)([^，,；。%+]{2,40}?)(?=，|,|额外|[+＋(]|$)/
    const m2 = re2.exec(t)
    if (!m2) return null
    perN = 1
    subject = m2[1]!
    const subStart = m2.index + m2[0].length - subject.length
    tailFromSubject = subStart >= 0 ? t.slice(subStart) : t
  }
  if (!Number.isFinite(perN) || perN <= 0 || !subject || subject.includes('层数上限')) return null
  const pct = parseBlessingMorePctFromSubjectTail(tailFromSubject, subject)
  if (pct == null || !Number.isFinite(pct)) return null
  return { perN, subject, perStackEquiv: pct / perN }
}

/** 与本条同时出现的「最多叠加 M 层」封顶 */
function parseBlessingDamageLineMaxStacks(line: string): number | null {
  const t = compactZhLine(line)
  const m = t.match(/最多叠(?:加|叕)?(\d+)(?:层|層)/)
  if (!m) return null
  const n = parseInt(m[1]!, 10)
  return Number.isFinite(n) && n > 0 ? n : null
}

type BlessingStackHitMoreResolved =
  | { kind: 'none' }
  | { kind: 'skip' }
  | {
      kind: 'ok'
      pct: number
      stacksUsed: number
      perStackEquiv: number
      subject: string
    }

function resolveBlessingStackHitMoreLine(
  line: string,
  getStacksForSubject: (subject: string) => number
): BlessingStackHitMoreResolved {
  const parsed = parsePerLayerSubjectScaledMore(line)
  if (!parsed) return { kind: 'none' }
  const autoTotal = getStacksForSubject(parsed.subject)
  const cap = parseBlessingDamageLineMaxStacks(line)
  const stacks = cap != null ? Math.min(autoTotal, cap) : autoTotal
  if (stacks <= 0) return { kind: 'skip' }
  return {
    kind: 'ok',
    pct: parsed.perStackEquiv * stacks,
    stacksUsed: stacks,
    perStackEquiv: parsed.perStackEquiv,
    subject: parsed.subject
  }
}

/**
 * 击中池 **额外 more %**：邻域须含「额外」且含伤害类关键词；排除持续/异常/暴击伤害专池（与 inc / 持续 / 暴击模块分工）。
 */
function extractHitDamageMorePctValuesFromLine(
  line: string,
  opts?: { playerDmgCtx?: PlayerDmgEffectLineCtx; primaryStats?: PrimaryStatsForScaling; skillKind?: SkillBaseDamageKind }
): number[] {
  const ctx = opts?.playerDmgCtx
  const prim = opts?.primaryStats
  const kind = opts?.skillKind ?? 'attack'
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const kwOpts: ExtractPctByKeywordsOpts = {
    requireAroundIncludes: '额外',
    skipAroundIncludesAny: [
      '持续伤害',
      '异常伤害',
      '暴击伤害',
      '受到的伤害',
      '承受的伤害',
      '受到的物理伤害',
      '受到的法术伤害',
      '来自近处敌人',
      '来自附近敌人'
    ],
    windowBefore: 48,
    windowAfter: 48
  }
  const dmgKeywords = ['伤害', '增伤', '伤害提高', '攻击伤害', '法术伤害', '元素伤害']

  const playerPartsOnly = filterPartsForPlayerGlobalDamageInc(line, ctx)
  const lineHasPlayerDmgKw = dmgKeywords.some(kw =>
    playerPartsOnly.some(p => p.replace(/\s+/g, '').includes(kw))
  )

  const out: number[] = []
  const skipPlainBonuses = prim ? new Map<number, number>() : undefined

  if (prim && skipPlainBonuses) {
    const joinedNorm = normalizeEveryNPrimarySyntax(
      playerPartsOnly.map(p => p.replace(/\s+/g, '')).join('')
    )
    const rePair = /每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)[^%]{0,80}?([+＋]?\d+(?:\.\d+)?)%/g
    let pm: RegExpExecArray | null
    while ((pm = rePair.exec(joinedNorm)) !== null) {
      const interval = parseFloat(pm[1]!)
      const attr = pm[2] as keyof PrimaryStatsForScaling
      const bonus = parseFloat(pm[3]!.replace(/^[+＋]/, ''))
      if (!Number.isFinite(interval) || interval <= 0 || !Number.isFinite(bonus)) continue
      const frag = pm[0]!
      if (!frag.includes('额外')) continue
      if (frag.includes('暴击伤害')) continue
      if (['持续伤害', '异常伤害', '受到的伤害', '承受的伤害'].some(s => frag.includes(s))) continue
      if (hitDamageMoreTextIsIncomingDamageTaken(frag)) continue
      const ok = dmgKeywords.some(k => frag.includes(k)) || lineHasPlayerDmgKw
      if (!ok) continue
      const st = prim[attr]
      if (!Number.isFinite(st)) continue
      out.push((bonus * st) / interval)
      skipPlainBonuses.set(bonus, (skipPlainBonuses.get(bonus) ?? 0) + 1)
    }
  }

  for (const part of parts) {
    if (part.includes('转化为')) continue
    if (effectClauseSkipForPlayerGlobalDamageInc(part, ctx)) continue
    if (!damageMorePartAppliesToSkill(part, kind)) continue
    const t = part.replace(/\s+/g, '')
    if (hitDamageMoreTextIsIncomingDamageTaken(part)) continue
    if (prim) {
      const segs = perPointPrimaryPctScaledSegments(t, prim, around => {
        if (!around.includes('额外')) return false
        if (['持续伤害', '异常伤害', '暴击伤害', '受到的伤害', '承受的伤害'].some(s => around.includes(s)))
          return false
        if (hitDamageMoreTextIsIncomingDamageTaken(around)) return false
        return dmgKeywords.some(k => around.includes(k))
      })
      const ranges = segs.map(s => ({ start: s.start, end: s.end }))
      out.push(
        ...extractPctValuesByKeywordsOnCompact(t, dmgKeywords, kwOpts, ranges, skipPlainBonuses)
      )
      for (const s of segs) out.push(s.scaledPct)
    } else {
      out.push(...extractPctValuesByKeywords(part, dmgKeywords, kwOpts))
    }
  }
  return out
}

/**
 * 持续伤害专用 inc：邻域须含「持续伤害」，且不与击中池、转伤/召唤/哨卫/转嫁规则混用。
 * 有 primaryStats 时：`X%每N点属性` 与「每N点…+X%持续伤害」配对均按除法缩放。
 */
function extractDotDamageIncPctValuesFromLine(
  line: string,
  opts?: { playerDmgCtx?: PlayerDmgEffectLineCtx; primaryStats?: PrimaryStatsForScaling }
): number[] {
  const ctx = opts?.playerDmgCtx
  const prim = opts?.primaryStats
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const kwOpts: ExtractPctByKeywordsOpts = {
    skipMatchIfAroundIncludes: '额外',
    requireAroundIncludes: '持续伤害',
    windowBefore: 40,
    windowAfter: 20
  }
  const playerPartsOnly = filterPartsForPlayerGlobalDamageInc(line, ctx)
  const lineHasPlayerDotKw = playerPartsOnly.some(p => p.replace(/\s+/g, '').includes('持续伤害'))

  const out: number[] = []
  const skipPlainBonuses = prim ? new Map<number, number>() : undefined

  if (prim && skipPlainBonuses) {
    const joinedNorm = normalizeEveryNPrimarySyntax(
      playerPartsOnly.map(p => p.replace(/\s+/g, '')).join('')
    )
    const rePair = /每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)[^%]{0,80}?([+＋]?\d+(?:\.\d+)?)%/g
    let pm: RegExpExecArray | null
    while ((pm = rePair.exec(joinedNorm)) !== null) {
      const interval = parseFloat(pm[1]!)
      const attr = pm[2] as keyof PrimaryStatsForScaling
      const bonus = parseFloat(pm[3]!.replace(/^[+＋]/, ''))
      if (!Number.isFinite(interval) || interval <= 0 || !Number.isFinite(bonus)) continue
      const frag = pm[0]!
      const ok = frag.includes('持续伤害') || lineHasPlayerDotKw
      if (!ok) continue
      const st = prim[attr]
      if (!Number.isFinite(st)) continue
      out.push((bonus * st) / interval)
      skipPlainBonuses.set(bonus, (skipPlainBonuses.get(bonus) ?? 0) + 1)
    }
  }

  for (const part of parts) {
    if (part.includes('转化为')) continue
    if (effectClauseSkipForPlayerGlobalDamageInc(part, ctx)) continue
    const t = part.replace(/\s+/g, '')
    if (prim) {
      const segs = perPointPrimaryPctScaledSegments(t, prim, around => {
        if (around.includes('额外')) return false
        return around.includes('持续伤害')
      })
      const ranges = segs.map(s => ({ start: s.start, end: s.end }))
      out.push(
        ...extractPctValuesByKeywordsOnCompact(t, ['持续伤害'], kwOpts, ranges, skipPlainBonuses)
      )
      for (const s of segs) out.push(s.scaledPct)
    } else {
      out.push(...extractPctValuesByKeywords(part, ['持续伤害'], kwOpts))
    }
  }
  return out
}

function critDamagePartAppliesToSkill(part: string, kind: SkillBaseDamageKind): boolean {
  const t = part.replace(/\s+/g, '')
  if (t.includes('法术暴击伤害')) return kind === 'spell'
  if (t.includes('攻击暴击伤害')) return kind === 'attack'
  return true
}

/**
 * 击中池 **暴击伤害提高 %**（邻域须含「暴击伤害」，排除「暴击伤害减免」等）。
 * 「法术/攻击暴击伤害」按当前技能类型过滤。
 */
function extractCritDamageIncPctValuesFromLine(
  line: string,
  opts?: {
    playerDmgCtx?: PlayerDmgEffectLineCtx
    primaryStats?: PrimaryStatsForScaling
    skillKind?: SkillBaseDamageKind
  }
): number[] {
  const ctx = opts?.playerDmgCtx
  const prim = opts?.primaryStats
  const kind = opts?.skillKind ?? 'attack'
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const kwOpts: ExtractPctByKeywordsOpts = {
    skipMatchIfAroundIncludes: '额外',
    skipAroundIncludesAny: ['减免', '持续伤害', '异常伤害', '受到的'],
    requireAroundIncludes: '暴击伤害',
    windowBefore: 40,
    windowAfter: 20
  }
  const dmgKw = ['暴击伤害']

  const out: number[] = []
  const skipPlainBonuses = prim ? new Map<number, number>() : undefined

  if (prim && skipPlainBonuses) {
    const playerPartsOnly = filterPartsForPlayerGlobalDamageInc(line, ctx)
    const joinedNorm = normalizeEveryNPrimarySyntax(
      playerPartsOnly.map(p => p.replace(/\s+/g, '')).join('')
    )
    const rePair = /每(\d+(?:\.\d+)?)点(力量|敏捷|智慧)[^%]{0,80}?([+＋]?\d+(?:\.\d+)?)%/g
    let pm: RegExpExecArray | null
    while ((pm = rePair.exec(joinedNorm)) !== null) {
      const interval = parseFloat(pm[1]!)
      const attr = pm[2] as keyof PrimaryStatsForScaling
      const bonus = parseFloat(pm[3]!.replace(/^[+＋]/, ''))
      if (!Number.isFinite(interval) || interval <= 0 || !Number.isFinite(bonus)) continue
      const frag = pm[0]!
      if (!frag.includes('暴击伤害') || frag.includes('减免') || frag.includes('受到的')) continue
      if (!critDamagePartAppliesToSkill(frag, kind)) continue
      const st = prim[attr]
      if (!Number.isFinite(st)) continue
      out.push((bonus * st) / interval)
      skipPlainBonuses.set(bonus, (skipPlainBonuses.get(bonus) ?? 0) + 1)
    }
  }

  for (const part of parts) {
    if (part.includes('转化为')) continue
    if (effectClauseSkipForPlayerGlobalDamageInc(part, ctx)) continue
    if (!critDamagePartAppliesToSkill(part, kind)) continue
    const t = part.replace(/\s+/g, '')
    if (!t.includes('暴击伤害')) continue
    if (t.includes('暴击伤害减免')) continue
    if (t.includes('受到的')) continue
    if (prim) {
      const segs = perPointPrimaryPctScaledSegments(t, prim, around => {
        if (around.includes('额外')) return false
        if (around.includes('减免')) return false
        if (around.includes('受到的')) return false
        return around.includes('暴击伤害')
      })
      const ranges = segs.map(s => ({ start: s.start, end: s.end }))
      out.push(...extractPctValuesByKeywordsOnCompact(t, dmgKw, kwOpts, ranges, skipPlainBonuses))
      for (const s of segs) out.push(s.scaledPct)
    } else {
      out.push(...extractPctValuesByKeywords(part, dmgKw, kwOpts))
    }
  }
  return out
}

/** 按子句拆分后再做关键词 % 提取；与 playerDmgCtx 联用过滤召唤/智械/哨卫子句 */
function extractPctValuesByKeywordsByClauses(
  line: string,
  keywords: string[],
  baseOpts: ExtractPctByKeywordsOpts | undefined,
  playerDmgCtx: PlayerDmgEffectLineCtx | undefined
): number[] {
  const parts = splitLineIntoEffectClauses(line)
  if (parts.length === 0) return []
  const out: number[] = []
  for (const part of parts) {
    if (playerDmgCtx && effectClauseSkipForPlayerDmgPool(part, playerDmgCtx)) continue
    out.push(...extractPctValuesByKeywords(part, keywords, baseOpts))
  }
  return out
}

function extractPctValuesByKeywords(
  text: string,
  keywords: string[],
  opts?: ExtractPctByKeywordsOpts
): number[] {
  if (!text.trim() || keywords.length === 0) return []
  const t = text.replace(/\s+/g, '')
  return extractPctValuesByKeywordsOnCompact(t, keywords, opts, [])
}

type PctLineSource = { label: string; pct: number; annotationSuffix?: string }

function truncateEffectLabel(line: string, maxLen = 88): string {
  const t = line.replace(/\s+/g, ' ').trim()
  if (t.length <= maxLen) return t
  return `${t.slice(0, maxLen)}…`
}

/** 与天赋/追忆共用：从纯文本效果行提取伤害 inc、攻速 inc、施法 inc（关键词邻近的 x%），并保留逐行来源 */
function resolvePctBucketsFromEffectLinesDetailed(
  rows: string[],
  opts?: {
    playerDmgCtx?: PlayerDmgEffectLineCtx
    /** 装备粗算三维，用于「每点力量」等词条后缀 */
    primaryStats?: { 力量: number; 敏捷: number; 智慧: number }
    skillKind?: SkillBaseDamageKind
  }
): {
  damageIncPct: number
  dotDamageIncPct: number
  attackSpeedIncPct: number
  castSpeedIncPct: number
  critDamageIncPct: number
  matchedLines: number
  totalEffectLines: number
  damageSources: PctLineSource[]
  dotDamageSources: PctLineSource[]
  critDamageSources: PctLineSource[]
  hitDamageMoreSources: PctLineSource[]
  attackSpeedSources: PctLineSource[]
  castSpeedSources: PctLineSource[]
} {
  const ctx = opts?.playerDmgCtx
  const prim = opts?.primaryStats
  let damageIncPct = 0
  let dotDamageIncPct = 0
  let attackSpeedIncPct = 0
  let castSpeedIncPct = 0
  let critDamageIncPct = 0
  let matchedLines = 0
  const damageSources: PctLineSource[] = []
  const dotDamageSources: PctLineSource[] = []
  const critDamageSources: PctLineSource[] = []
  const hitDamageMoreSources: PctLineSource[] = []
  const attackSpeedSources: PctLineSource[] = []
  const castSpeedSources: PctLineSource[] = []

  for (const line of rows) {
    let matched = false
    const attackSpeedVals = extractSpeedIncPctValuesFromLine(line, ['攻击速度', '攻速'], ctx, prim)
    if (attackSpeedVals.length) {
      const sum = attackSpeedVals.reduce((a, b) => a + b, 0)
      attackSpeedIncPct += sum
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      attackSpeedSources.push({
        label: truncateEffectLabel(line),
        pct: sum,
        annotationSuffix: sfx || undefined
      })
      matched = true
    }
    const castSpeedVals = extractSpeedIncPctValuesFromLine(line, ['施法速度', '施法'], ctx, prim)
    if (castSpeedVals.length) {
      const sum = castSpeedVals.reduce((a, b) => a + b, 0)
      castSpeedIncPct += sum
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      castSpeedSources.push({
        label: truncateEffectLabel(line),
        pct: sum,
        annotationSuffix: sfx || undefined
      })
      matched = true
    }
    const damageVals = extractDamageIncPctValuesFromLine(line, { playerDmgCtx: ctx, primaryStats: prim })
    if (damageVals.length) {
      const sum = damageVals.reduce((a, b) => a + b, 0)
      damageIncPct += sum
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      damageSources.push({
        label: truncateEffectLabel(line),
        pct: sum,
        annotationSuffix: sfx || undefined
      })
      matched = true
    }
    const dotVals = extractDotDamageIncPctValuesFromLine(line, { playerDmgCtx: ctx, primaryStats: prim })
    if (dotVals.length) {
      const sum = dotVals.reduce((a, b) => a + b, 0)
      dotDamageIncPct += sum
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      dotDamageSources.push({
        label: truncateEffectLabel(line),
        pct: sum,
        annotationSuffix: sfx || undefined
      })
      matched = true
    }
    const critDmgVals = extractCritDamageIncPctValuesFromLine(line, {
      playerDmgCtx: ctx,
      primaryStats: prim,
      skillKind: opts?.skillKind
    })
    if (critDmgVals.length) {
      const sum = critDmgVals.reduce((a, b) => a + b, 0)
      critDamageIncPct += sum
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      critDamageSources.push({
        label: truncateEffectLabel(line),
        pct: sum,
        annotationSuffix: sfx || undefined
      })
      matched = true
    }
    const hitMoreVals = extractHitDamageMorePctValuesFromLine(line, {
      playerDmgCtx: ctx,
      primaryStats: prim,
      skillKind: opts?.skillKind
    })
    if (hitMoreVals.length) {
      const sfx = prim ? perPointPrimaryAnnotationSuffix(line, prim) : ''
      for (const p of hitMoreVals) {
        if (!Number.isFinite(p) || p === 0) continue
        hitDamageMoreSources.push({
          label: truncateEffectLabel(line),
          pct: p,
          annotationSuffix: sfx || undefined
        })
      }
      matched = true
    }
    if (matched) matchedLines++
  }
  return {
    damageIncPct,
    dotDamageIncPct,
    attackSpeedIncPct,
    castSpeedIncPct,
    critDamageIncPct,
    matchedLines,
    totalEffectLines: rows.length,
    damageSources,
    dotDamageSources,
    critDamageSources,
    hitDamageMoreSources,
    attackSpeedSources,
    castSpeedSources
  }
}

/** 装备词条粗算三维，仅用于「每点力量」类天赋/追忆行的展示后缀 */
const buildPrimaryStatsForAnnotation = computed(() => {
  const eq = buildStore.snapshot.equipment as Record<string, unknown>
  return {
    力量: estimatePrimaryStatFlatFromEquipment(eq, '力量'),
    敏捷: estimatePrimaryStatFlatFromEquipment(eq, '敏捷'),
    智慧: estimatePrimaryStatFlatFromEquipment(eq, '智慧')
  }
})

/** 暴击伤害解析共用：玩家池 ctx、粗算三维、当前技能类型 */
const critDamageExtractOpts = computed(() => ({
  playerDmgCtx: {
    allowSummonMinionKeywords: dmgIncludeSummonMinionStatLines.value,
    coreSkillIsSentry: coreSkillIsSentryType(previewSkills.value as Record<string, unknown>)
  } as PlayerDmgEffectLineCtx,
  primaryStats: buildPrimaryStatsForAnnotation.value,
  skillKind: dmgSkillKind.value
}))

/** 装备各槽解析到的暴击伤害提高 %（当前技能池，含每点属性缩放） */
const dmgEquipmentCritDamageSourceRows = computed(() => {
  const eq = buildStore.snapshot.equipment as Record<string, unknown>
  const equipped = Array.isArray(eq?.equipped) ? eq.equipped : []
  const o = critDamageExtractOpts.value
  const rows: { slotIndex: number; snippet: string; pct: number }[] = []
  for (let i = 0; i < equipped.length; i++) {
    if (equipped[i] == null) continue
    for (const raw of getResolvedEffectLinesForEquipmentSlot(eq, i)) {
      const line = stripHtmlLikeText(String(raw ?? ''))
      if (!line) continue
      const vals = extractCritDamageIncPctValuesFromLine(line, o)
      const sum = vals.reduce((a, b) => a + b, 0)
      if (sum !== 0) {
        rows.push({ slotIndex: i, snippet: truncateEffectLabel(line), pct: sum })
      }
    }
  }
  return rows
})

/** 已选契灵 effectLines 中的暴击伤害 % */
const critDamagePactLineRows = computed(() => {
  const p = previewPact.value
  const rows: { label: string; pct: number }[] = []
  if (!p || typeof p !== 'object' || Number(p.v) !== PACTSPIRIT_SNAPSHOT_V) return rows
  const battle = Array.isArray(p.selectedBattleIds) ? p.selectedBattleIds : []
  const drop = Array.isArray(p.selectedDropIds) ? p.selectedDropIds : []
  const catalog = (
    pactspiritCatalogJson as { items?: { id?: string; name?: string; effectLines?: string[] }[] }
  ).items ?? []
  const byId = new Map(catalog.map(it => [String(it.id ?? '').trim(), it]))
  const o = critDamageExtractOpts.value
  for (const rawId of [...battle, ...drop]) {
    const id = String(rawId ?? '').trim()
    if (!id) continue
    const it = byId.get(id)
    const name = String(it?.name ?? pactIdToName.get(id) ?? id)
    for (const fx of it?.effectLines ?? []) {
      const line = stripHtmlLikeText(String(fx ?? ''))
      if (!line) continue
      const vals = extractCritDamageIncPctValuesFromLine(line, o)
      const sum = vals.reduce((a, b) => a + b, 0)
      if (sum !== 0) rows.push({ label: `契灵 · ${name} · ${truncateEffectLabel(line)}`, pct: sum })
    }
  }
  return rows
})

/** 核心 + 四个主动槽成长文案中的暴击伤害 %（按当前等级行） */
const critDamageCoreActiveLineRows = computed(() => {
  const s = previewSkills.value
  if (!s || typeof s !== 'object' || Number(s.v) !== SKILLS_SNAPSHOT_V) return []
  const o = critDamageExtractOpts.value
  const rows: { label: string; pct: number }[] = []
  const core = normalizeSkillLink(s.core)
  const actives = Array.isArray(s.active) ? s.active.map(normalizeSkillLink) : []
  const links: { slotLabel: string; link: ReturnType<typeof normalizeSkillLink> }[] = [
    { slotLabel: '核心', link: core },
    ...actives.map((link, i) => ({ slotLabel: `主动 ${i + 1}`, link }))
  ]
  for (const { slotLabel, link } of links) {
    const mainId = String(link.mainSkillId ?? '').trim()
    if (!mainId) continue
    const lv = Number.isFinite(link.mainSkillLevel as number)
      ? Math.max(1, Math.floor(link.mainSkillLevel as number))
      : 20
    const growth = activeSkillGrowthLinesById.get(mainId)
    const rawLine = growth?.[lv - 1]
    if (!rawLine) continue
    const line = stripHtmlLikeText(rawLine)
    if (!line) continue
    const vals = extractCritDamageIncPctValuesFromLine(line, o)
    const sum = vals.reduce((a, b) => a + b, 0)
    if (sum !== 0) {
      rows.push({
        label: `${slotLabel} · ${skillLabel(mainId)} Lv.${lv} · ${truncateEffectLabel(line)}`,
        pct: sum
      })
    }
  }
  return rows
})

/** 常见祝福满层层数估算（装备 + 天赋；其它名称仅在命中词条时按需计算） */
const autoBlessingStacksSummaryRows = computed(() =>
  COMMON_BLESSING_NAMES_FOR_UI.map(subject => ({
    subject,
    stacks: estimateBlessingStacksFromBuild(subject)
  }))
)

/** 装备各槽：击中 more（邻域含「额外」，按条连乘） */
const dmgEquipmentHitMoreSourceRows = computed(() => {
  const eq = buildStore.snapshot.equipment as Record<string, unknown>
  const equipped = Array.isArray(eq?.equipped) ? eq.equipped : []
  const o = critDamageExtractOpts.value
  const stackMemo = new Map<string, number>()
  const getStacksForSubject = (subject: string) => {
    if (!stackMemo.has(subject)) stackMemo.set(subject, estimateBlessingStacksFromBuild(subject))
    return stackMemo.get(subject)!
  }
  const rows: { slotIndex: number; snippet: string; pct: number }[] = []
  for (let i = 0; i < equipped.length; i++) {
    if (equipped[i] == null) continue
    for (const raw of getResolvedEffectLinesForEquipmentSlot(eq, i)) {
      const line = stripHtmlLikeText(String(raw ?? ''))
      if (!line) continue
      const br = resolveBlessingStackHitMoreLine(line, getStacksForSubject)
      if (br.kind === 'skip') continue
      if (br.kind === 'ok') {
        if (Number.isFinite(br.pct) && br.pct !== 0) {
          rows.push({
            slotIndex: i,
            snippet: `${truncateEffectLabel(line)}（${br.subject} ${br.stacksUsed} 层）`,
            pct: br.pct
          })
        }
        continue
      }
      for (const p of extractHitDamageMorePctValuesFromLine(line, o)) {
        if (Number.isFinite(p) && p !== 0) {
          rows.push({ slotIndex: i, snippet: truncateEffectLabel(line), pct: p })
        }
      }
    }
  }
  return rows
})

/** 契灵 effectLines 中的击中 more %（每条单独连乘） */
const dmgPactHitMoreLineRows = computed(() => {
  const p = previewPact.value
  const rows: { label: string; pct: number }[] = []
  if (!p || typeof p !== 'object' || Number(p.v) !== PACTSPIRIT_SNAPSHOT_V) return rows
  const battle = Array.isArray(p.selectedBattleIds) ? p.selectedBattleIds : []
  const drop = Array.isArray(p.selectedDropIds) ? p.selectedDropIds : []
  const catalog = (
    pactspiritCatalogJson as { items?: { id?: string; name?: string; effectLines?: string[] }[] }
  ).items ?? []
  const byId = new Map(catalog.map(it => [String(it.id ?? '').trim(), it]))
  const o = critDamageExtractOpts.value
  const stackMemo = new Map<string, number>()
  const getStacksForSubject = (subject: string) => {
    if (!stackMemo.has(subject)) stackMemo.set(subject, estimateBlessingStacksFromBuild(subject))
    return stackMemo.get(subject)!
  }
  for (const rawId of [...battle, ...drop]) {
    const id = String(rawId ?? '').trim()
    if (!id) continue
    const it = byId.get(id)
    const name = String(it?.name ?? pactIdToName.get(id) ?? id)
    for (const fx of it?.effectLines ?? []) {
      const line = stripHtmlLikeText(String(fx ?? ''))
      if (!line) continue
      const br = resolveBlessingStackHitMoreLine(line, getStacksForSubject)
      if (br.kind === 'skip') continue
      if (br.kind === 'ok') {
        if (Number.isFinite(br.pct) && br.pct !== 0) {
          rows.push({
            label: `契灵 · ${name} · ${truncateEffectLabel(line)}（${br.subject} ${br.stacksUsed} 层）`,
            pct: br.pct
          })
        }
        continue
      }
      for (const pct of extractHitDamageMorePctValuesFromLine(line, o)) {
        if (Number.isFinite(pct) && pct !== 0) {
          rows.push({ label: `契灵 · ${name} · ${truncateEffectLabel(line)}`, pct })
        }
      }
    }
  }
  return rows
})

/** 核心 / 主动成长文案：击中 more % */
const dmgCoreActiveHitMoreLineRows = computed(() => {
  const s = previewSkills.value
  if (!s || typeof s !== 'object' || Number(s.v) !== SKILLS_SNAPSHOT_V) return []
  const o = critDamageExtractOpts.value
  const rows: { label: string; pct: number }[] = []
  const core = normalizeSkillLink(s.core)
  const actives = Array.isArray(s.active) ? s.active.map(normalizeSkillLink) : []
  const links: { slotLabel: string; link: ReturnType<typeof normalizeSkillLink> }[] = [
    { slotLabel: '核心', link: core },
    ...actives.map((link, i) => ({ slotLabel: `主动 ${i + 1}`, link }))
  ]
  for (const { slotLabel, link } of links) {
    const mainId = String(link.mainSkillId ?? '').trim()
    if (!mainId) continue
    const lv = Number.isFinite(link.mainSkillLevel as number)
      ? Math.max(1, Math.floor(link.mainSkillLevel as number))
      : 20
    const growth = activeSkillGrowthLinesById.get(mainId)
    const rawLine = growth?.[lv - 1]
    if (!rawLine) continue
    const line = stripHtmlLikeText(rawLine)
    if (!line) continue
    for (const pct of extractHitDamageMorePctValuesFromLine(line, o)) {
      if (Number.isFinite(pct) && pct !== 0) {
        rows.push({
          label: `${slotLabel} · ${skillLabel(mainId)} Lv.${lv} · ${truncateEffectLabel(line)}`,
          pct
        })
      }
    }
  }
  return rows
})

const dmgTalentResolved = computed(() => {
  const rows: string[] = professionTalentStore
    .getAllocatedEffects()
    .map(x => stripHtmlLikeText(String(x ?? '')))
    .filter(Boolean)
  return resolvePctBucketsFromEffectLinesDetailed(rows, {
    playerDmgCtx: {
      allowSummonMinionKeywords: dmgIncludeSummonMinionStatLines.value,
      coreSkillIsSentry: coreSkillIsSentryType(previewSkills.value as Record<string, unknown>)
    },
    primaryStats: buildPrimaryStatsForAnnotation.value,
    skillKind: dmgSkillKind.value
  })
})

const memoryEffectLinesForCalc = computed(() => {
  const mf = flattenMemories(buildStore.snapshot.memories)
  return [...mf.bases, ...mf.implicit, ...mf.random]
    .map(r => stripHtmlLikeText(String(r.effectText ?? '')))
    .filter(Boolean)
})

/** 伤害公式：英雄特性相关 more 的等级基准（与追忆「+N 英雄特性等级」叠加） */
const DEFAULT_DMG_HERO_TRAIT_LEVEL = 3

function parseHeroTraitLevelBonusFromMemoryLines(lines: readonly string[]): number {
  let sum = 0
  for (const line of lines) {
    const t = line.replace(/\s+/g, '')
    let m: RegExpExecArray | null
    const re1 = /\+(\d+(?:\.\d+)?)英雄特性等级/g
    while ((m = re1.exec(t)) !== null) {
      const n = parseFloat(m[1]!)
      if (Number.isFinite(n)) sum += n
    }
    const re2 = /英雄特性等级\+(\d+(?:\.\d+)?)/g
    while ((m = re2.exec(t)) !== null) {
      const n = parseFloat(m[1]!)
      if (Number.isFinite(n)) sum += n
    }
  }
  return sum
}

/** 「每 1 等级 / 每级 … 额外 …%」类：解析出的 % 按每级生效，总系数 × 特性等级 */
function heroTraitMoreLineIsPerLevelExtra(line: string): boolean {
  const t = line.replace(/\s+/g, '')
  if (!t.includes('额外')) return false
  if (t.includes('每点')) return false
  if (/每\d*等级/.test(t)) return true
  return t.includes('每级')
}

const dmgHeroTraitLevelBonusFromMemories = computed(() =>
  parseHeroTraitLevelBonusFromMemoryLines(memoryEffectLinesForCalc.value)
)

/** 用于缩放英雄特性击中 more：默认 3 级 + 追忆词条累加，限制在 1–20 */
const dmgHeroTraitEffectiveLevel = computed(() => {
  const raw = DEFAULT_DMG_HERO_TRAIT_LEVEL + dmgHeroTraitLevelBonusFromMemories.value
  const n = Math.round(raw)
  if (!Number.isFinite(n)) return DEFAULT_DMG_HERO_TRAIT_LEVEL
  return Math.min(Math.max(n, 1), 20)
})

/** 天赋效果行中的暴击值解析（按条） */
const critTalentLineRows = computed(() => {
  const rows: { origin: string; label: string; contributions: CritContribution[] }[] = []
  for (const raw of professionTalentStore.getAllocatedEffects()) {
    const line = stripHtmlLikeText(String(raw ?? ''))
    if (!line) continue
    const cs = parseCritContributionsFromEffectLine(line)
    if (!cs.length) continue
    rows.push({ origin: '天赋', label: truncateCritEffectLabel(line), contributions: cs })
  }
  return rows
})

/** 追忆已选词缀文案中的暴击值解析（按条） */
const critMemoryLineRows = computed(() => {
  const rows: { origin: string; label: string; contributions: CritContribution[] }[] = []
  for (const line of memoryEffectLinesForCalc.value) {
    const cs = parseCritContributionsFromEffectLine(line)
    if (!cs.length) continue
    rows.push({ origin: '追忆', label: truncateCritEffectLabel(line), contributions: cs })
  }
  return rows
})

const passiveCritPoolPct = computed(() =>
  dmgSkillKind.value === 'attack'
    ? skillDerivedSummary.value.passiveCritPctAttack
    : skillDerivedSummary.value.passiveCritPctSpell
)

const passiveCritUiRows = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  return skillDerivedSummary.value.passiveCritRows
    .map(r => ({
      label: r.label,
      pct: sumCritContributionsForKind(r.contributions, k, 'pct'),
      flat: sumCritContributionsForKind(r.contributions, k, 'flat')
    }))
    .filter(r => r.pct !== 0 || r.flat !== 0)
})

/** 已选英雄特性在图鉴中的 effects 文案（与英雄页数据源一致） */
const heroTraitEffectLinesForConversion = computed(() => {
  const h = previewHero.value
  if (!h || typeof h !== 'object' || Number(h.v) !== HERO_SNAPSHOT_V) return []
  const entry = heroCatalogEntry.value
  const traits = entry?.traits
  if (!Array.isArray(traits) || traits.length === 0) return []
  const rawSel = h.selectedTraitByRequiredLevel
  if (!rawSel || typeof rawSel !== 'object') return []
  const names = new Set(
    Object.values(rawSel as Record<string, unknown>)
      .map(x => String(x ?? '').trim())
      .filter(Boolean)
  )
  if (names.size === 0) return []
  const lines: string[] = []
  for (const t of traits) {
    const nm = String(t.name ?? '').trim()
    if (!nm || !names.has(nm)) continue
    const eff = t.effects
    if (!Array.isArray(eff)) continue
    for (const e of eff) {
      const clean = stripHtmlLikeText(String(e ?? ''))
      if (clean) lines.push(clean)
    }
  }
  return lines
})

/** 已选英雄特性 effect 行中的暴击值 */
const critHeroTraitCritLineRows = computed(() => {
  const rows: { origin: string; label: string; contributions: CritContribution[] }[] = []
  for (const line of heroTraitEffectLinesForConversion.value) {
    const cs = parseCritContributionsFromEffectLine(line)
    if (!cs.length) continue
    rows.push({ origin: '英雄特性', label: truncateCritEffectLabel(line), contributions: cs })
  }
  return rows
})

/** 英雄特性文案中的「暴击伤害」%（按当前技能类型过滤法术/攻击暴击伤害） */
const critDamageHeroTraitLineRows = computed(() => {
  const o = critDamageExtractOpts.value
  const rows: { label: string; pct: number }[] = []
  for (const line of heroTraitEffectLinesForConversion.value) {
    const vals = extractCritDamageIncPctValuesFromLine(line, o)
    const sum = vals.reduce((a, b) => a + b, 0)
    if (sum !== 0) rows.push({ label: `英雄特性 · ${truncateEffectLabel(line)}`, pct: sum })
  }
  return rows
})

/** 英雄特性：击中 more %（邻域含「额外」，每条连乘；按特性等级缩放，追忆「+N 英雄特性等级」累加，默认 Lv.3） */
const dmgHeroHitMoreLineRows = computed(() => {
  const o = critDamageExtractOpts.value
  const L = dmgHeroTraitEffectiveLevel.value
  const perLevelDefault = DEFAULT_DMG_HERO_TRAIT_LEVEL
  const rows: { label: string; pct: number }[] = []
  for (const line of heroTraitEffectLinesForConversion.value) {
    // 怒火等：「非爆裂技能额外 -80% 伤害」为对非爆裂条的单独规则，不计入本页通用击中 more 连乘
    if (line.replace(/\s+/g, '').includes('非爆裂技能')) continue
    const perLv = heroTraitMoreLineIsPerLevelExtra(line)
    for (const pct of extractHitDamageMorePctValuesFromLine(line, o)) {
      if (!Number.isFinite(pct) || pct === 0) continue
      const scaled = perLv ? pct * L : (pct * L) / perLevelDefault
      const scaleNote = perLv ? `每级×Lv.${L}` : `Lv.${L}/Lv.${perLevelDefault}`
      rows.push({
        label: `英雄特性 · ${truncateEffectLabel(line)}（${scaleNote}）`,
        pct: scaled
      })
    }
  }
  return rows
})

const critMiscLineUiRows = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  const out: { origin: string; label: string; pct: number; flat: number }[] = []
  for (const r of [
    ...critTalentLineRows.value,
    ...critMemoryLineRows.value,
    ...critHeroTraitCritLineRows.value
  ]) {
    const pct = sumCritContributionsForKind(r.contributions, k, 'pct')
    const flat = sumCritContributionsForKind(r.contributions, k, 'flat')
    if (pct !== 0 || flat !== 0) out.push({ origin: r.origin, label: r.label, pct, flat })
  }
  return out
})

const dmgConversionSourceBundles = computed((): DamageConversionSourceBundle[] => {
  const bundles: DamageConversionSourceBundle[] = []
  const eq = buildStore.snapshot.equipment as Record<string, unknown>
  const equipped = Array.isArray(eq?.equipped) ? eq.equipped : []
  for (let i = 0; i < equipped.length; i++) {
    if (equipped[i] == null) continue
    const lines = getResolvedEffectLinesForEquipmentSlot(eq, i)
    if (lines.length) {
      bundles.push({
        id: `equipment-${i}`,
        label: `装备 · ${equipmentSlotLabel(i)}`,
        lines
      })
    }
  }
  const talentLines = professionTalentStore.getAllocatedEffectRawLines()
  if (talentLines.length) {
    bundles.push({ id: 'talent', label: '天赋（已加点）', lines: talentLines })
  }
  const memLines = memoryEffectLinesForCalc.value
  if (memLines.length) {
    bundles.push({ id: 'memory', label: '追忆', lines: memLines })
  }
  const p = previewPact.value
  if (p && typeof p === 'object' && Number(p.v) === PACTSPIRIT_SNAPSHOT_V) {
    const battle = Array.isArray(p.selectedBattleIds) ? p.selectedBattleIds : []
    const drop = Array.isArray(p.selectedDropIds) ? p.selectedDropIds : []
    const catalog = (
      pactspiritCatalogJson as { items?: { id?: string; name?: string; effectLines?: string[] }[] }
    ).items ?? []
    const byId = new Map(catalog.map(it => [String(it.id ?? '').trim(), it]))
    for (const rawId of [...battle, ...drop]) {
      const id = String(rawId ?? '').trim()
      if (!id) continue
      const it = byId.get(id)
      const fx = (it?.effectLines ?? []).map(x => String(x).trim()).filter(Boolean)
      if (!fx.length) continue
      bundles.push({
        id: `pact-${id}`,
        label: `契灵 · ${String(it?.name ?? pactIdToName.get(id) ?? id)}`,
        lines: fx
      })
    }
  }
  const heroFx = heroTraitEffectLinesForConversion.value
  if (heroFx.length) {
    bundles.push({ id: 'hero-traits', label: '英雄特性（已选）', lines: heroFx })
  }
  return bundles
})

const dmgMemoryResolved = computed(() =>
  resolvePctBucketsFromEffectLinesDetailed(memoryEffectLinesForCalc.value, {
    playerDmgCtx: {
      allowSummonMinionKeywords: dmgIncludeSummonMinionStatLines.value,
      coreSkillIsSentry: coreSkillIsSentryType(previewSkills.value as Record<string, unknown>)
    },
    primaryStats: buildPrimaryStatsForAnnotation.value,
    skillKind: dmgSkillKind.value
  })
)

/** 核心槽主技能标签含力量/敏捷/智慧时：每 1 点对应属性 → 0.5% 击中 more（属性为装备粗算合计，与本页 inc 后缀一致） */
const SKILL_TAG_PRIMARY_STAT_MORE_PER_POINT = 0.5
const PRIMARY_STAT_ATTRIBUTE_TAGS = ['力量', '敏捷', '智慧'] as const

const dmgCoreSkillPrimaryStatMore = computed((): { pct: number; label: string } | null => {
  const id = coreMainSkillId.value.trim()
  if (!id) return null
  const tags = activeSkillTagById.get(id) ?? []
  const attrs = PRIMARY_STAT_ATTRIBUTE_TAGS.filter(a => tags.includes(a))
  if (!attrs.length) return null
  const prim = buildPrimaryStatsForAnnotation.value
  let sumStat = 0
  const bits: string[] = []
  for (const a of attrs) {
    const v = prim[a]
    if (Number.isFinite(v) && v > 0) {
      sumStat += v
      bits.push(`${a} ${format4(v)}`)
    }
  }
  if (sumStat <= 0 || !bits.length) return null
  const pct = SKILL_TAG_PRIMARY_STAT_MORE_PER_POINT * sumStat
  const nm = skillLabel(id)
  return {
    pct,
    label: `核心「${nm}」标签主属性 (${bits.join('，')}) × ${SKILL_TAG_PRIMARY_STAT_MORE_PER_POINT}% / 点`
  }
})

/** 天赋/追忆（勾选时）+ 装备 + 契灵 + 英雄特性 + 核心/主动成长：击中 more % 列表，与手填、技能链路一并逐项连乘 */
const dmgAllAutoMorePctList = computed(() => {
  const out: number[] = []
  const pushFinite = (n: number) => {
    if (Number.isFinite(n) && n !== 0) out.push(n)
  }
  if (dmgUseTalentAuto.value) {
    for (const s of dmgTalentResolved.value.hitDamageMoreSources) pushFinite(s.pct)
  }
  if (dmgUseMemoryAuto.value) {
    for (const s of dmgMemoryResolved.value.hitDamageMoreSources) pushFinite(s.pct)
  }
  for (const r of dmgEquipmentHitMoreSourceRows.value) pushFinite(r.pct)
  for (const r of dmgPactHitMoreLineRows.value) pushFinite(r.pct)
  for (const r of dmgHeroHitMoreLineRows.value) pushFinite(r.pct)
  for (const r of dmgCoreActiveHitMoreLineRows.value) pushFinite(r.pct)
  return out
})

/** 各模块解析到的暴击伤害提高 % 加总（不与击中 inc 相加） */
const dmgCritDamageAutoIncPct = computed(() => {
  let s = skillDerivedSummary.value.passiveCritDamageIncPct
  if (dmgUseTalentAuto.value) s += dmgTalentResolved.value.critDamageIncPct
  if (dmgUseMemoryAuto.value) s += dmgMemoryResolved.value.critDamageIncPct
  for (const r of critDamageHeroTraitLineRows.value) s += r.pct
  for (const r of dmgEquipmentCritDamageSourceRows.value) s += r.pct
  for (const r of critDamagePactLineRows.value) s += r.pct
  for (const r of critDamageCoreActiveLineRows.value) s += r.pct
  return s
})

/**
 * 手填暴击倍率 M 与自动解析的「暴击伤害提高%」合并：1 + (M−1)×(1 + Σ%/100)（演示口径）。
 */
const dmgResolvedCritStrikeMultiplier = computed(() => {
  const cm = dmgCritMult.value
  const hand = cm != null && Number.isFinite(cm) ? cm : 1
  const h = Math.max(1, hand)
  const inc = dmgCritDamageAutoIncPct.value
  if (!Number.isFinite(inc) || inc <= 0) return h
  return Math.max(1, 1 + (h - 1) * (1 + inc / 100))
})

const dmgIncSourceRows = computed(() => {
  const rows: { label: string; pct: number | null }[] = []
  const hand =
    dmgIncreased.value != null && Number.isFinite(dmgIncreased.value) ? dmgIncreased.value : null
  rows.push({ label: '手填「提高类总和」', pct: hand })
  if (dmgUseTalentAuto.value) {
    for (const s of dmgTalentResolved.value.damageSources) {
      rows.push({
        label: `天赋 · ${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  if (dmgUseMemoryAuto.value) {
    for (const s of dmgMemoryResolved.value.damageSources) {
      rows.push({
        label: `追忆 · ${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  const totalPct = rows.reduce(
    (a, r) => a + (r.pct != null && Number.isFinite(r.pct) ? r.pct : 0),
    0
  )
  return { rows, totalPct }
})

const dotIncSourceRows = computed(() => {
  const rows: { label: string; pct: number | null }[] = []
  const hand =
    dmgDotIncreased.value != null && Number.isFinite(dmgDotIncreased.value)
      ? dmgDotIncreased.value
      : null
  rows.push({ label: '手填「持续伤害提高类总和」', pct: hand })
  if (dmgUseTalentAuto.value) {
    for (const s of dmgTalentResolved.value.dotDamageSources) {
      rows.push({
        label: `天赋 · ${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  if (dmgUseMemoryAuto.value) {
    for (const s of dmgMemoryResolved.value.dotDamageSources) {
      rows.push({
        label: `追忆 · ${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  const totalPct = rows.reduce(
    (a, r) => a + (r.pct != null && Number.isFinite(r.pct) ? r.pct : 0),
    0
  )
  return { rows, totalPct }
})

const resolvedDotBaseFlat = computed(() =>
  Math.max(0, Number.isFinite(dmgDotBase.value) ? dmgDotBase.value : 0)
)

const dotMoreMultiplierOnly = computed(() =>
  moreMultiplierFromList(parseMoreList(dmgDotMoreListStr.value))
)

const dmgMoreDisplayRows = computed(() => {
  const hand = dmgHandMoreSources.value
  const skill = skillDerivedSummary.value.damageMoreSources
  const rows: { origin: string; label: string; pct: number }[] = [
    ...hand.map(h => ({ ...h, origin: '手填' as const })),
    ...skill.map(s => ({ ...s, origin: '技能链路' as const }))
  ]
  const psMore = dmgCoreSkillPrimaryStatMore.value
  if (psMore && Number.isFinite(psMore.pct) && psMore.pct !== 0) {
    rows.push({ origin: '核心·主属性', label: psMore.label, pct: psMore.pct })
  }
  if (dmgUseTalentAuto.value) {
    for (const s of dmgTalentResolved.value.hitDamageMoreSources) {
      rows.push({
        origin: '天赋',
        label: `${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  if (dmgUseMemoryAuto.value) {
    for (const s of dmgMemoryResolved.value.hitDamageMoreSources) {
      rows.push({
        origin: '追忆',
        label: `${s.label}${s.annotationSuffix ?? ''}`,
        pct: s.pct
      })
    }
  }
  for (const r of dmgEquipmentHitMoreSourceRows.value) {
    rows.push({
      origin: '装备',
      label: `${equipmentSlotLabel(r.slotIndex)} · ${r.snippet}`,
      pct: r.pct
    })
  }
  for (const r of dmgPactHitMoreLineRows.value) {
    rows.push({ origin: '契灵', label: r.label, pct: r.pct })
  }
  for (const r of dmgHeroHitMoreLineRows.value) {
    rows.push({ origin: '英雄特性', label: r.label, pct: r.pct })
  }
  for (const r of dmgCoreActiveHitMoreLineRows.value) {
    rows.push({ origin: '主动/核心', label: r.label, pct: r.pct })
  }
  return rows
})

const dmgMorePctAlgebraicSum = computed(() =>
  dmgMoreDisplayRows.value.reduce((a, r) => a + (Number.isFinite(r.pct) ? r.pct : 0), 0)
)

const dmgEquipmentCritPctSources = computed(() =>
  equipmentAttackStatEst.value.sources.filter(s => s.kind === 'critValuePct')
)
const dmgEquipmentCritFlatSources = computed(() =>
  equipmentAttackStatEst.value.sources.filter(s => s.kind === 'critValueFlat')
)

const dmgEquipmentCritPctSourcesForPool = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  return dmgEquipmentCritPctSources.value.filter(s => critScopeAppliesToSkill(s.critScope, k))
})
const dmgEquipmentCritFlatSourcesForPool = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  return dmgEquipmentCritFlatSources.value.filter(s => critScopeAppliesToSkill(s.critScope, k))
})
const dmgEquipmentAttackSpeedSources = computed(() =>
  equipmentAttackStatEst.value.sources.filter(s => s.kind === 'attackSpeedInc')
)
const dmgEquipmentBaseApsSources = computed(() =>
  equipmentAttackStatEst.value.sources.filter(s => s.kind === 'baseAps')
)

const critValuePctSourcesSum = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  let s =
    k === 'attack'
      ? skillDerivedSummary.value.passiveCritPctAttack
      : skillDerivedSummary.value.passiveCritPctSpell
  for (const x of dmgEquipmentCritPctSourcesForPool.value) {
    if (Number.isFinite(x.value)) s += x.value
  }
  for (const r of critTalentLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'pct')
  }
  for (const r of critMemoryLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'pct')
  }
  for (const r of critHeroTraitCritLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'pct')
  }
  return s
})

const critValueFlatSourcesSum = computed(() => {
  const k = dmgSkillKind.value === 'attack' ? 'attack' : 'spell'
  let s =
    k === 'attack'
      ? skillDerivedSummary.value.passiveCritFlatAttack
      : skillDerivedSummary.value.passiveCritFlatSpell
  for (const x of dmgEquipmentCritFlatSourcesForPool.value) {
    if (Number.isFinite(x.value)) s += x.value
  }
  for (const r of critTalentLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'flat')
  }
  for (const r of critMemoryLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'flat')
  }
  for (const r of critHeroTraitCritLineRows.value) {
    s += sumCritContributionsForKind(r.contributions, k, 'flat')
  }
  return s
})

/** 当前技能池下暴击值有效合计：平值加总 × (1 + %加总/100)，与同页武器物理段一致 */
const critValueEffectiveCombined = computed(() => {
  const flat = critValueFlatSourcesSum.value
  const pct = critValuePctSourcesSum.value
  const f = Number.isFinite(flat) ? flat : 0
  const p = Number.isFinite(pct) ? pct : 0
  return f * (1 + p / 100)
})

/**
 * 面板暴击率（%）= 有效暴击值 / 100（例 2230 → 22.3%）。
 * 伤害公式内概率（0–1）= 该百分比 / 100 = min(1, 有效暴击值 / 10000)，超过 100% 按 100% 封顶。
 */
const dmgResolvedCritChance = computed(() => {
  const v = critValueEffectiveCombined.value
  const n = Number.isFinite(v) && v > 0 ? v : 0
  return Math.min(1, n / 10000)
})

const dotDmgBreakdown = computed(() => {
  const base = Math.max(0, Number.isFinite(dmgDotBase.value) ? dmgDotBase.value : 0)
  return estimateExpectedHitDamage({
    base,
    increasedPctTotal: dotIncSourceRows.value.totalPct,
    morePctList: parseMoreList(dmgDotMoreListStr.value),
    enemyResistPct: Number.isFinite(dmgResistPct.value) ? dmgResistPct.value : 0,
    critChance: dmgResolvedCritChance.value,
    critStrikeMultiplier: dmgResolvedCritStrikeMultiplier.value,
    otherIndependentMultiplier: Number.isFinite(dmgOtherMult.value) ? dmgOtherMult.value : 1
  })
})

const dotDps = computed(() => {
  const tps = Math.max(0, Number.isFinite(dmgDotTicksPerSecond.value) ? dmgDotTicksPerSecond.value : 0)
  return dotDmgBreakdown.value.expectedDamage * tps
})

const critAutoSourcesEmpty = computed(
  () =>
    dmgEquipmentCritPctSourcesForPool.value.length === 0 &&
    dmgEquipmentCritFlatSourcesForPool.value.length === 0 &&
    passiveCritUiRows.value.length === 0 &&
    critMiscLineUiRows.value.length === 0
)

const dmgSpeedIncSourceRows = computed(() => {
  const rows: { label: string; pct: number | null }[] = []
  const hand =
    dmgSpeedInc.value != null && Number.isFinite(dmgSpeedInc.value) ? dmgSpeedInc.value : null
  rows.push({
    label: dmgSkillKind.value === 'attack' ? '手填「攻击速度 inc 总和」' : '手填「施法速度 inc 总和」',
    pct: hand
  })
  if (dmgSkillKind.value === 'attack') {
    for (const s of dmgEquipmentAttackSpeedSources.value) {
      rows.push({
        label: `装备 · ${equipmentSlotLabel(s.slotIndex)} · ${s.snippet}`,
        pct: s.value
      })
    }
    if (skillDerivedSummary.value.attackSpeedIncPct !== 0) {
      rows.push({
        label: '被动技能（攻速，面板/描述解析合计）',
        pct: skillDerivedSummary.value.attackSpeedIncPct
      })
    }
    if (dmgUseTalentAuto.value) {
      for (const s of dmgTalentResolved.value.attackSpeedSources) {
        rows.push({
          label: `天赋 · ${s.label}${s.annotationSuffix ?? ''}`,
          pct: s.pct
        })
      }
    }
    if (dmgUseMemoryAuto.value) {
      for (const s of dmgMemoryResolved.value.attackSpeedSources) {
        rows.push({
          label: `追忆 · ${s.label}${s.annotationSuffix ?? ''}`,
          pct: s.pct
        })
      }
    }
  } else {
    if (skillDerivedSummary.value.castSpeedIncPct !== 0) {
      rows.push({
        label: '被动技能（施法，面板/描述解析合计）',
        pct: skillDerivedSummary.value.castSpeedIncPct
      })
    }
    if (dmgUseTalentAuto.value) {
      for (const s of dmgTalentResolved.value.castSpeedSources) {
        rows.push({
          label: `天赋 · ${s.label}${s.annotationSuffix ?? ''}`,
          pct: s.pct
        })
      }
    }
    if (dmgUseMemoryAuto.value) {
      for (const s of dmgMemoryResolved.value.castSpeedSources) {
        rows.push({
          label: `追忆 · ${s.label}${s.annotationSuffix ?? ''}`,
          pct: s.pct
        })
      }
    }
  }
  const totalPct = rows.reduce(
    (a, r) => a + (r.pct != null && Number.isFinite(r.pct) ? r.pct : 0),
    0
  )
  return { rows, totalPct }
})

const dmgSpeedMoreAlgebraicSum = computed(() =>
  parseMoreList(dmgSpeedMoreStr.value).reduce((a, n) => a + (Number.isFinite(n) ? n : 0), 0)
)

const weaponPhysicalEst = computed(() =>
  estimatePhysicalAttackFlatFromEquipment(
    buildStore.snapshot.equipment as Record<string, unknown>
  )
)

/** 多来源伤害转化：独立解析与展示，不参与 estimateDps / inc/more 连乘 */
const dmgConversionEst = computed(() =>
  estimateDamageConversionFromSourceBundles(dmgConversionSourceBundles.value)
)

const equipmentAttackStatEst = computed(() =>
  estimateAttackStatsFromEquipmentDetailed(buildStore.snapshot.equipment as Record<string, unknown>)
)

const resolvedWeaponPhysicalFlat = computed(() => {
  if (dmgWeaponManual.value) {
    return Number.isFinite(dmgWeaponBaseManual.value) ? Math.max(0, dmgWeaponBaseManual.value) : 0
  }
  return weaponPhysicalEst.value.totalPhysicalFlat
})

const resolvedBasePerSecond = computed(() => {
  if (dmgSkillKind.value !== 'attack') {
    return Number.isFinite(dmgBasePerSecond.value) ? dmgBasePerSecond.value : 0
  }
  if (dmgUseWeaponBaseSpeedAuto.value && equipmentAttackStatEst.value.baseAttackPerSecond > 0) {
    return equipmentAttackStatEst.value.baseAttackPerSecond
  }
  return Number.isFinite(dmgBasePerSecond.value) ? dmgBasePerSecond.value : 0
})

const dmgBreakdown = computed(() => {
  const kind = dmgSkillKind.value
  const base = effectiveBaseFlatDamage({
    kind,
    weaponBaseFlat: resolvedWeaponPhysicalFlat.value,
    skillBaseFlat: dmgSpellBase.value
  })
  return estimateExpectedHitDamage({
    base,
    baseKind: kind,
    increasedPctTotal:
      (dmgIncreased.value != null && Number.isFinite(dmgIncreased.value) ? dmgIncreased.value : 0) +
      (dmgUseTalentAuto.value ? dmgTalentResolved.value.damageIncPct : 0) +
      (dmgUseMemoryAuto.value ? dmgMemoryResolved.value.damageIncPct : 0),
    morePctList: [
      ...parseMoreList(dmgMoreListStr.value),
      ...supportMorePctFromAllLinks.value,
      ...(dmgCoreSkillPrimaryStatMore.value && dmgCoreSkillPrimaryStatMore.value.pct !== 0
        ? [dmgCoreSkillPrimaryStatMore.value.pct]
        : []),
      ...dmgAllAutoMorePctList.value
    ],
    enemyResistPct: Number.isFinite(dmgResistPct.value) ? dmgResistPct.value : 0,
    critChance: dmgResolvedCritChance.value,
    critStrikeMultiplier: dmgResolvedCritStrikeMultiplier.value,
    otherIndependentMultiplier: Number.isFinite(dmgOtherMult.value) ? dmgOtherMult.value : 1
  })
})

const dmgSpeedBreakdown = computed(() =>
  estimateHitsPerSecond({
    basePerSecond: resolvedBasePerSecond.value,
    speedIncreasedPctTotal:
      (dmgSpeedInc.value != null && Number.isFinite(dmgSpeedInc.value) ? dmgSpeedInc.value : 0) +
      (dmgSkillKind.value === 'attack' ? equipmentAttackStatEst.value.attackSpeedIncPct : 0) +
      (dmgSkillKind.value === 'attack'
        ? skillDerivedSummary.value.attackSpeedIncPct
        : skillDerivedSummary.value.castSpeedIncPct) +
      (dmgUseTalentAuto.value
        ? dmgSkillKind.value === 'attack'
          ? dmgTalentResolved.value.attackSpeedIncPct
          : dmgTalentResolved.value.castSpeedIncPct
        : 0) +
      (dmgUseMemoryAuto.value
        ? dmgSkillKind.value === 'attack'
          ? dmgMemoryResolved.value.attackSpeedIncPct
          : dmgMemoryResolved.value.castSpeedIncPct
        : 0),
    speedMorePctList: parseMoreList(dmgSpeedMoreStr.value)
  })
)

const dmgDps = computed(() =>
  estimateDps(dmgBreakdown.value, dmgSpeedBreakdown.value, dmgSkillKind.value)
)

const selectedHeroTraitNames = computed(() => heroPreviewRows.value.map(x => x.name))
const isAngerHero = computed(() => previewHeroId.value === 'Anger')
const angerHasFuryTrait = computed(() => selectedHeroTraitNames.value.includes('怒火'))
const showAngerBurstPanel = computed(() => isAngerHero.value && angerHasFuryTrait.value)
const angerAutoParams = computed(() => ({
  burstHitScale: 1,
  rage: 100,
  furyTraitLevel: 3,
  guciLevel: 3,
  yuanzuiLevel: 3,
  jingqingLevel: 3,
  // 攻速相关加成由当前装备自动解析
  attackSpeedRelatedBonusPct: Math.max(0, equipmentAttackStatEst.value.attackSpeedIncPct)
}))

const angerBurstBreakdown = computed(() => {
  const baseSingle = Math.max(0, dmgBreakdown.value.expectedDamage)
  const scale = angerAutoParams.value.burstHitScale
  const burstBonusPct = totalAngerDamageBonusPct(
    angerAutoParams.value.rage,
    angerAutoParams.value.furyTraitLevel,
    angerAutoParams.value.guciLevel,
    angerAutoParams.value.yuanzuiLevel
  )
  const burstSingle = baseSingle * scale * (1 + burstBonusPct / 100)
  const cdModel = effectiveBurstIntervalSec(
    angerAutoParams.value.attackSpeedRelatedBonusPct,
    angerAutoParams.value.jingqingLevel
  )
  const cdLimited = cdModel.intervalSec > 0 ? 1 / cdModel.intervalSec : 0
  const hitLimited = Math.max(0, dmgSpeedBreakdown.value.hitsPerSecond)
  const tps = Math.min(hitLimited, cdLimited)
  const burstDps = burstSingle * tps
  const mainSkillDpsAfterPenalty =
    dmgDps.value.dps *
    (angerApplyNonBurstPenalty.value && angerAutoParams.value.guciLevel >= 1 ? 0.2 : 1)
  const total = mainSkillDpsAfterPenalty + (angerBurstIncludeInDps.value ? burstDps : 0)
  return {
    burstBonusPct,
    singleExpectedDamage: burstSingle,
    intervalSec: cdModel.intervalSec,
    triggersPerSecond: tps,
    burstDps,
    mainSkillDpsAfterPenalty,
    totalDpsWithBurst: total
  }
})

/** 伤害与中间量展示：千分位、禁止科学计数法；极小正数多保留几位小数以免全被舍成 0 */
function format4(n: number): string {
  if (!Number.isFinite(n)) return '—'
  const abs = Math.abs(n)
  const maxFrac = abs > 0 && abs < 0.01 ? 10 : 6
  return n.toLocaleString('zh-CN', {
    minimumFractionDigits: 0,
    maximumFractionDigits: maxFrac,
    useGrouping: true
  })
}

/** 来源列表中的 % 列：手填未输入时显示 — */
function formatIncRowPct(pct: number | null | undefined): string {
  if (pct == null || !Number.isFinite(pct)) return '—'
  return `${format4(pct)}%`
}

const heroJson = ref(JSON.stringify(snapshot.value.hero, null, 2))
const skillsJson = ref(JSON.stringify(snapshot.value.skills, null, 2))
const equipmentJson = ref(JSON.stringify(snapshot.value.equipment, null, 2))
const pactspiritJson = ref(JSON.stringify(snapshot.value.pactspirit, null, 2))

function syncHeroJsonFromSnapshot() {
  const s = JSON.stringify(snapshot.value.hero, null, 2)
  if (heroJson.value !== s) heroJson.value = s
}
function syncSkillsJsonFromSnapshot() {
  const s = JSON.stringify(snapshot.value.skills, null, 2)
  if (skillsJson.value !== s) skillsJson.value = s
}
function syncEquipmentJsonFromSnapshot() {
  const s = JSON.stringify(snapshot.value.equipment, null, 2)
  if (equipmentJson.value !== s) equipmentJson.value = s
}
function syncPactspiritJsonFromSnapshot() {
  const s = JSON.stringify(snapshot.value.pactspirit, null, 2)
  if (pactspiritJson.value !== s) pactspiritJson.value = s
}

function syncAllBuildJsonTextareasFromSnapshot() {
  syncHeroJsonFromSnapshot()
  syncSkillsJsonFromSnapshot()
  syncEquipmentJsonFromSnapshot()
  syncPactspiritJsonFromSnapshot()
}

onMounted(syncAllBuildJsonTextareasFromSnapshot)
onActivated(syncAllBuildJsonTextareasFromSnapshot)

watch(() => snapshot.value.hero, syncHeroJsonFromSnapshot, { deep: true })
watch(() => snapshot.value.skills, syncSkillsJsonFromSnapshot, { deep: true })
watch(() => snapshot.value.equipment, syncEquipmentJsonFromSnapshot, { deep: true })
watch(() => snapshot.value.pactspirit, syncPactspiritJsonFromSnapshot, { deep: true })

function safeParseRecord(text: string): Record<string, unknown> | null {
  try {
    const parsed = JSON.parse(text)
    if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
      return parsed as Record<string, unknown>
    }
  } catch {
    // ignore invalid json
  }
  return null
}

function saveAllJson() {
  const hero = safeParseRecord(heroJson.value)
  const skills = safeParseRecord(skillsJson.value)
  const equipment = safeParseRecord(equipmentJson.value)
  const pact = safeParseRecord(pactspiritJson.value)
  if (hero) buildStore.setHero(hero)
  if (skills) buildStore.setSkills(skills)
  if (equipment) buildStore.setEquipment(equipment)
  if (pact) buildStore.setPactspirit(pact)
}

/** 从 buildStore 当前快照刷新四个 JSON 区；天赋/追忆与 store 联动，会一并更新。 */
function recalculateFromBuild() {
  syncAllBuildJsonTextareasFromSnapshot()
}

const talentSummaryText = computed(() => JSON.stringify(buildStore.snapshot.talent, null, 2))
const memoriesSummaryText = computed(() => JSON.stringify(buildStore.snapshot.memories, null, 2))

function resetAll() {
  buildStore.resetAll()
  heroJson.value = '{}'
  skillsJson.value = '{}'
  equipmentJson.value = '{}'
  pactspiritJson.value = '{}'
}
</script>

<style scoped>
.calc-page {
  box-sizing: border-box;
  min-height: calc(100dvh - var(--app-header-height, 4.75rem));
  padding: 16px;
  color: #fff;
}

.calc-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.calc-head h2 {
  margin: 0;
}

.calc-actions {
  display: flex;
  gap: 8px;
}

.btn {
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.08);
  color: #fff;
  border-radius: 8px;
  padding: 7px 12px;
  cursor: pointer;
}

.btn-secondary {
  border-color: rgba(125, 211, 252, 0.35);
  color: #bae6fd;
  background: rgba(56, 189, 248, 0.1);
}

.btn-secondary:hover {
  background: rgba(56, 189, 248, 0.18);
}

.btn.danger {
  border-color: rgba(255, 99, 99, 0.45);
  color: #ffd1d1;
}

.calc-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(280px, 1fr));
  gap: 12px;
}

.card {
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 10px;
  background: rgba(0, 0, 0, 0.24);
  padding: 12px;
}

.card h3 {
  margin: 0 0 8px;
  font-size: 14px;
}

.editor {
  width: 100%;
  min-height: 170px;
  box-sizing: border-box;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  padding: 8px;
  font-family: Consolas, monospace;
  font-size: 12px;
}

.readout {
  margin: 0;
  min-height: 170px;
  max-height: 260px;
  overflow: auto;
  padding: 8px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.35);
  border: 1px solid rgba(255, 255, 255, 0.12);
  font-size: 12px;
}

.calc-json-block {
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.calc-json-title {
  margin: 0 0 6px;
  font-size: 15px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.88);
}

.calc-json-hint {
  margin: 0 0 12px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.45);
}

.calc-preview-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.sp-card--wide {
  grid-column: 1 / -1;
}

.sp-card-title {
  margin: 0 0 10px;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.92);
}

.sp-empty {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.38);
}

.sp-muted {
  color: rgba(255, 255, 255, 0.42);
  font-size: 12px;
}

.sp-warn {
  margin: 0 0 8px;
  font-size: 11px;
  line-height: 1.4;
  color: #fde68a;
  padding: 6px 8px;
  border-radius: 6px;
  background: rgba(251, 191, 36, 0.12);
  border: 1px solid rgba(251, 191, 36, 0.28);
}

.sp-sub {
  margin: 8px 0 0;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.4);
}

.sp-id {
  font-family: ui-monospace, Consolas, monospace;
  font-size: 11px;
  color: rgba(125, 211, 252, 0.85);
}

.sp-chip {
  display: inline-flex;
  align-items: center;
  padding: 2px 8px;
  border-radius: 999px;
  font-size: 11px;
  border: 1px solid rgba(255, 255, 255, 0.18);
  background: rgba(0, 0, 0, 0.35);
  color: rgba(230, 237, 255, 0.92);
}

.sp-chip--hero {
  border-color: rgba(233, 69, 96, 0.45);
  background: rgba(233, 69, 96, 0.15);
}

.sp-chip--legend {
  border-color: rgba(168, 85, 247, 0.45);
  color: #e9d5ff;
}

.sp-chip--crafted {
  border-color: rgba(56, 189, 248, 0.4);
  color: #bae6fd;
}

.sp-chip--talent {
  margin-right: 6px;
  margin-bottom: 4px;
}

.sp-chip--on {
  border-color: rgba(52, 211, 153, 0.5);
  color: #a7f3d0;
}

.sp-hero-head {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.sp-hero-head--rich {
  align-items: flex-start;
  gap: 12px;
}

.sp-hero-portrait-wrap {
  flex-shrink: 0;
  width: 52px;
  height: 52px;
  border-radius: 10px;
  overflow: hidden;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.35);
}

.sp-hero-portrait {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sp-hero-text {
  flex: 1;
  min-width: 0;
}

.sp-hero-title-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.sp-hero-sub {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.4;
  margin-bottom: 4px;
}

.sp-hero-meta-line {
  font-size: 11px;
  color: rgba(251, 191, 36, 0.85);
}

.sp-hero-trait-empty {
  margin: 8px 0 0;
  line-height: 1.45;
}

.sp-trait-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sp-trait-line {
  display: flex;
  align-items: baseline;
  gap: 10px;
  font-size: 12px;
}

.sp-trait-lv {
  flex-shrink: 0;
  min-width: 2.5rem;
  color: rgba(251, 191, 36, 0.9);
  font-variant-numeric: tabular-nums;
}

.sp-trait-name {
  color: rgba(230, 237, 255, 0.92);
}

.sp-skill-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sp-skill-row {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sp-skill-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.sp-skill-label {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}

.sp-skill-body {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.sp-affix-chip {
  display: inline-block;
  max-width: 100%;
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 11px;
  line-height: 1.35;
  background: rgba(233, 69, 96, 0.12);
  border: 1px solid rgba(233, 69, 96, 0.28);
  color: rgba(255, 228, 232, 0.95);
  word-break: break-word;
}

.sp-affix-chip--main {
  background: rgba(56, 189, 248, 0.12);
  border-color: rgba(56, 189, 248, 0.35);
  color: #e0f2fe;
}

.sp-affix-chip--eq {
  background: rgba(0, 0, 0, 0.32);
  border-color: rgba(255, 255, 255, 0.12);
  color: rgba(220, 230, 255, 0.88);
}

.sp-affix-chip--mem {
  background: rgba(167, 139, 250, 0.12);
  border-color: rgba(167, 139, 250, 0.35);
  color: #ede9fe;
  margin-right: 6px;
  margin-bottom: 4px;
}

.sp-equip-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.sp-equip-row {
  display: grid;
  grid-template-columns: 4.5rem 1fr;
  gap: 8px 12px;
  align-items: start;
  padding-bottom: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}

.sp-equip-row:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.sp-equip-slot {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.48);
}

.sp-equip-main {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  font-size: 12px;
}

.sp-equip-name {
  color: rgba(255, 255, 255, 0.92);
  font-weight: 500;
}

.sp-equip-affix-hint {
  font-size: 10px;
  color: rgba(255, 255, 255, 0.38);
}

.sp-equip-effects {
  grid-column: 1 / -1;
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sp-pact-block {
  margin-top: 10px;
}

.sp-pact-block:first-of-type {
  margin-top: 0;
}

.sp-pact-head {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  margin-bottom: 6px;
}

.sp-pact-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.sp-pact-empty {
  font-size: 12px;
}

.sp-talent-summary {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin-bottom: 8px;
}

.sp-talent-prof {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.sp-talent-prof-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  font-size: 12px;
}

.sp-mem-block {
  margin-bottom: 12px;
}

.sp-mem-block:last-child {
  margin-bottom: 0;
}

.sp-mem-k {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.5);
  margin-bottom: 6px;
}

.sp-mem-n {
  color: rgba(255, 255, 255, 0.35);
  font-weight: 400;
}

.sp-mem-v {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  align-items: flex-start;
}

.calc-raw-json {
  margin-top: 8px;
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  background: rgba(0, 0, 0, 0.2);
  padding: 8px 12px;
}

.calc-raw-json summary {
  cursor: pointer;
  font-size: 12px;
  color: rgba(125, 211, 252, 0.95);
  user-select: none;
}

.calc-raw-json summary:hover {
  color: #e0f2fe;
}

.calc-grid--raw {
  margin-top: 12px;
}

.dmg-demo {
  margin-top: 0;
}

.dmg-demo-hint {
  margin: 0 0 12px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(255, 255, 255, 0.55);
}

.dmg-demo-hint strong {
  color: rgba(255, 255, 255, 0.88);
  font-weight: 600;
}

.dmg-kind-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  font-size: 12px;
  color: rgba(220, 230, 255, 0.9);
}

.dmg-kind-label {
  color: rgba(255, 255, 255, 0.55);
}

.dmg-kind-auto-chip {
  display: inline-flex;
  align-items: center;
  border: 1px solid rgba(74, 158, 255, 0.35);
  background: rgba(74, 158, 255, 0.12);
  color: #d8e8ff;
  border-radius: 999px;
  padding: 2px 10px;
}

.dmg-kind-opt {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}

.dmg-kind-opt input {
  accent-color: #e94560;
}

.dmg-talent-auto {
  margin-bottom: 10px;
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 11px;
  color: rgba(255, 255, 255, 0.7);
}

.dmg-demo-stack {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 14px;
}

.dmg-cat {
  border-radius: 10px;
  padding: 12px 14px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.dmg-cat--muted {
  background: rgba(0, 0, 0, 0.16);
  border-color: rgba(255, 255, 255, 0.07);
}

.dmg-cat--dot {
  border-color: rgba(251, 191, 36, 0.28);
  box-shadow: inset 3px 0 0 rgba(251, 191, 36, 0.35);
}

.dmg-module-total {
  margin-top: 12px;
  padding-top: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.dmg-module-total--conversion {
  margin-top: 14px;
}

.dmg-module-total-line {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  line-height: 1.45;
}

.dmg-module-total-line--note {
  color: rgba(200, 210, 235, 0.72);
}

.dmg-module-total-line--note .dmg-module-total-val {
  color: rgba(251, 191, 36, 0.82);
}

.dmg-module-total-line--emph .dmg-module-total-label {
  font-weight: 600;
  color: #e8eeff;
}

/* 与「基础伤害」武器网格内 合计（公式用）的 strong 同色（#fbbf24） */
.dmg-module-total-line--emph .dmg-module-total-val {
  font-weight: 700;
  font-size: 1.05em;
  color: #fbbf24;
}

.dmg-module-total-label {
  color: rgba(220, 230, 255, 0.88);
}

.dmg-module-total-val {
  font-family: ui-monospace, Consolas, monospace;
  color: #fbbf24;
  font-size: 1.05em;
}

.dmg-cat-title {
  margin: 0 0 8px;
  font-size: 13px;
  font-weight: 600;
  color: #f0f4ff;
  letter-spacing: 0.02em;
}

.dmg-cat-summary {
  margin: 0 0 10px;
  font-size: 12px;
  line-height: 1.45;
  color: rgba(220, 230, 255, 0.88);
}

.dmg-cat-summary code {
  font-family: ui-monospace, Consolas, monospace;
  color: #7dd3fc;
}

.dmg-cat-hint {
  margin: 0 0 8px;
  line-height: 1.45;
}

.dmg-cat-body {
  margin-top: 4px;
}

.dmg-cat-empty {
  margin: 6px 0 0;
}

.dmg-src-list {
  list-style: none;
  margin: 8px 0 0;
  padding: 0;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.18);
  border: 1px solid rgba(255, 255, 255, 0.06);
}

.dmg-src-li {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px 10px;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  font-size: 11px;
  color: rgba(220, 230, 255, 0.82);
}

.dmg-src-li:last-child {
  border-bottom: none;
}

.dmg-src-li--note {
  display: block;
  font-size: 11px;
  color: rgba(200, 210, 235, 0.75);
  line-height: 1.4;
}

.dmg-src-label {
  flex: 1;
  min-width: 120px;
  color: rgba(255, 255, 255, 0.55);
}

.dmg-src-val {
  font-family: ui-monospace, Consolas, monospace;
  color: #93c5fd;
  flex-shrink: 0;
}

/* 列表内与「合计」同级的强调数值（如持续伤害 DPS 行） */
.dmg-src-li.dmg-line--result .dmg-src-val {
  color: #fbbf24;
  font-size: 1.05em;
}

.dmg-src-tag {
  flex-shrink: 0;
  font-size: 10px;
  padding: 1px 7px;
  border-radius: 4px;
  background: rgba(74, 158, 255, 0.2);
  color: #b8d4ff;
  border: 1px solid rgba(74, 158, 255, 0.35);
}

.dmg-weapon-auto--flat {
  padding: 0;
  background: transparent;
  border: none;
}

.dmg-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 12px;
  color: rgba(220, 230, 255, 0.85);
}

.dmg-field--wide {
  grid-column: 1 / -1;
}

.dmg-blessing-auto-list {
  margin: 0 0 8px;
  padding-left: 1.1rem;
  font-size: 12px;
  color: rgba(200, 214, 255, 0.88);
  list-style: disc;
}

.dmg-blessing-auto-list code {
  font-size: 13px;
  color: #e8f0ff;
}

.dmg-input {
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.16);
  background: rgba(0, 0, 0, 0.35);
  color: #fff;
  padding: 8px 10px;
  font-size: 13px;
}

.dmg-breakdown {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(233, 69, 96, 0.08);
  border: 1px solid rgba(233, 69, 96, 0.22);
}

.dmg-breakdown--speed {
  margin-top: 10px;
  background: rgba(56, 189, 248, 0.08);
  border-color: rgba(56, 189, 248, 0.28);
}

.dmg-breakdown--anger {
  margin-top: 10px;
  background: rgba(245, 158, 11, 0.08);
  border-color: rgba(245, 158, 11, 0.28);
}

.dmg-breakdown--conversion {
  margin-top: 10px;
  background: rgba(167, 139, 250, 0.08);
  border-color: rgba(167, 139, 250, 0.28);
}

.dmg-conversion-heading {
  margin: 0 0 6px;
  font-size: 14px;
  font-weight: 600;
  color: rgba(230, 220, 255, 0.95);
}

.dmg-conversion-summary {
  margin: 0 0 8px;
}

.dmg-conversion-slot {
  margin-top: 8px;
  padding: 8px 10px;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.08);
}

.dmg-conversion-slot-title {
  font-size: 12px;
  font-weight: 600;
  color: #c4b5fd;
  margin-bottom: 6px;
}

.dmg-conversion-seg-list {
  margin: 0;
  padding: 0;
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.dmg-conversion-seg {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 6px 8px;
  font-size: 12px;
  color: rgba(220, 230, 255, 0.88);
}

.dmg-conversion-pct {
  font-family: ui-monospace, Consolas, monospace;
  color: #ddd6fe;
  font-size: 0.95em;
}

.dmg-conversion-from,
.dmg-conversion-to {
  max-width: 100%;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.dmg-conversion-kw {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11px;
}

.dmg-conversion-raw {
  margin-top: 6px;
}

.dmg-demo-grid--mini {
  margin: 6px 0 10px;
}

.dmg-dps-val {
  color: #fbbf24 !important;
  font-size: 1.05em !important;
}

.dmg-line {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
  font-size: 12px;
  color: rgba(220, 230, 255, 0.85);
}

.dmg-line code {
  font-family: ui-monospace, Consolas, monospace;
  color: #7dd3fc;
  font-size: 0.95em;
}

.dmg-line--result {
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
}

.dmg-line--result strong {
  color: #fbbf24;
  font-size: 1.05em;
}

.dmg-sub {
  color: rgba(255, 255, 255, 0.45);
  font-size: 11px;
}

.dmg-field--check {
  flex-direction: row;
  align-items: flex-start;
  gap: 8px;
}

.dmg-check {
  margin-top: 2px;
  accent-color: #e94560;
}

.dmg-weapon-auto {
  grid-column: 1 / -1;
  padding: 10px 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.28);
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.dmg-weapon-auto-title {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.4;
  margin-bottom: 8px;
}

.dmg-weapon-auto-grid {
  display: grid;
  grid-template-columns: auto 1fr;
  gap: 6px 12px;
  align-items: center;
  font-size: 12px;
  color: rgba(220, 230, 255, 0.88);
}

.dmg-weapon-auto-grid code {
  font-family: ui-monospace, Consolas, monospace;
  color: #7dd3fc;
}

.dmg-weapon-auto-grid strong {
  color: #fbbf24;
  font-size: 1.05em;
}

.dmg-weapon-strike {
  color: #fde68a !important;
}

.dmg-other-slots-list {
  margin: 10px 0 0;
  padding: 8px 10px 6px;
  list-style: none;
  border-radius: 6px;
  background: rgba(0, 0, 0, 0.22);
  border: 1px solid rgba(255, 255, 255, 0.06);
  font-size: 11px;
}

.dmg-other-slots-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 10px;
  padding: 3px 0;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  color: rgba(220, 230, 255, 0.75);
}

.dmg-other-slots-item:last-child {
  border-bottom: none;
}

.dmg-other-slots-label {
  flex-shrink: 0;
  color: rgba(255, 255, 255, 0.5);
}

.dmg-other-slots-item code {
  font-family: ui-monospace, Consolas, monospace;
  color: #93c5fd;
  font-size: 11px;
}

@media (max-width: 900px) {
  .dmg-demo-stack .dmg-field {
    min-width: 0;
  }
}
</style>

