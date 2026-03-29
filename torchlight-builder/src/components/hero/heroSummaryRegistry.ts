import type { Component } from 'vue'
import HeroSummaryAnger from '@/components/hero/HeroSummaryAnger.vue'
import HeroSummarySeethingSilhouette from '@/components/hero/HeroSummarySeethingSilhouette.vue'
import HeroSummaryRangerOfGlory from '@/components/hero/HeroSummaryRangerOfGlory.vue'
import HeroSummaryLethalFlash from '@/components/hero/HeroSummaryLethalFlash.vue'
import HeroSummaryZealotOfWar from '@/components/hero/HeroSummaryZealotOfWar.vue'
import HeroSummaryWindStalker from '@/components/hero/HeroSummaryWindStalker.vue'
import HeroSummaryLightningShadow from '@/components/hero/HeroSummaryLightningShadow.vue'
import HeroSummaryVendettasSting from '@/components/hero/HeroSummaryVendettasSting.vue'
import HeroSummaryBlastNova from '@/components/hero/HeroSummaryBlastNova.vue'
import HeroSummaryCreativeGenius from '@/components/hero/HeroSummaryCreativeGenius.vue'
import HeroSummaryFlameOfPleasure from '@/components/hero/HeroSummaryFlameOfPleasure.vue'
import HeroSummaryFrostbittenHeart from '@/components/hero/HeroSummaryFrostbittenHeart.vue'
import HeroSummaryIceFireFusion from '@/components/hero/HeroSummaryIceFireFusion.vue'
import HeroSummaryWisdomOfTheGods from '@/components/hero/HeroSummaryWisdomOfTheGods.vue'
import HeroSummaryIncarnationOfTheGods from '@/components/hero/HeroSummaryIncarnationOfTheGods.vue'
import HeroSummaryBlasphemer from '@/components/hero/HeroSummaryBlasphemer.vue'
import HeroSummarySpacetimeIllusion from '@/components/hero/HeroSummarySpacetimeIllusion.vue'
import HeroSummarySpacetimeElapse from '@/components/hero/HeroSummarySpacetimeElapse.vue'
import HeroSummaryOrderCalling from '@/components/hero/HeroSummaryOrderCalling.vue'
import HeroSummaryChargeCalling from '@/components/hero/HeroSummaryChargeCalling.vue'
import HeroSummaryHighCourtChariot from '@/components/hero/HeroSummaryHighCourtChariot.vue'
import HeroSummaryUnsulliedBlade from '@/components/hero/HeroSummaryUnsulliedBlade.vue'
import HeroSummaryGrowingBreeze from '@/components/hero/HeroSummaryGrowingBreeze.vue'
import HeroSummaryVigilantBreeze from '@/components/hero/HeroSummaryVigilantBreeze.vue'
import HeroSummarySingWithTheTide from '@/components/hero/HeroSummarySingWithTheTide.vue'

/** 与 `Hero.vue` 中 hero-summary 一致：hero.id → 专属数值 Summary 组件 */
export const heroSummaryMap: Record<string, Component> = {
  Anger: HeroSummaryAnger,
  Seething_Silhouette: HeroSummarySeethingSilhouette,
  Ranger_of_Glory: HeroSummaryRangerOfGlory,
  Lethal_Flash: HeroSummaryLethalFlash,
  Zealot_of_War: HeroSummaryZealotOfWar,
  Wind_Stalker: HeroSummaryWindStalker,
  Lightning_Shadow: HeroSummaryLightningShadow,
  'Vendetta%27s_Sting': HeroSummaryVendettasSting,
  Blast_Nova: HeroSummaryBlastNova,
  Creative_Genius: HeroSummaryCreativeGenius,
  Flame_of_Pleasure: HeroSummaryFlameOfPleasure,
  Frostbitten_Heart: HeroSummaryFrostbittenHeart,
  'Ice-Fire_Fusion': HeroSummaryIceFireFusion,
  Wisdom_of_The_Gods: HeroSummaryWisdomOfTheGods,
  Incarnation_of_the_Gods: HeroSummaryIncarnationOfTheGods,
  Blasphemer: HeroSummaryBlasphemer,
  Spacetime_Illusion: HeroSummarySpacetimeIllusion,
  Spacetime_Elapse: HeroSummarySpacetimeElapse,
  Order_Calling: HeroSummaryOrderCalling,
  Charge_Calling: HeroSummaryChargeCalling,
  High_Court_Chariot: HeroSummaryHighCourtChariot,
  Unsullied_Blade: HeroSummaryUnsulliedBlade,
  Growing_Breeze: HeroSummaryGrowingBreeze,
  Vigilant_Breeze: HeroSummaryVigilantBreeze,
  Sing_with_the_Tide: HeroSummarySingWithTheTide
}
