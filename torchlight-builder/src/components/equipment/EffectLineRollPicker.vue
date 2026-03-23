<template>
  <span v-if="!segments" class="equipment-effect-plain">{{ line }}</span>
  <span v-else class="equipment-effect-line-roll">
    <template v-for="(seg, si) in segments" :key="si">
      <span v-if="seg.type === 'text'" class="equipment-effect-line-piece">{{ seg.text }}</span>
      <select
        v-else
        class="effect-roll-select"
        :aria-label="'选择词条数值'"
        :value="pickValue(si)"
        @change="onSelectChange(si, ($event.target as HTMLSelectElement).value)"
      >
        <option v-for="opt in seg.options" :key="opt" :value="opt">{{ opt }}</option>
      </select>
    </template>
  </span>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue'
import { parseEffectLineRolls } from '@/utils/effectLineRolls'

const props = defineProps<{
  line: string
  pickKeyPrefix: string
  selections: Record<string, string>
}>()

const emit = defineEmits<{
  (e: 'set-pick', key: string, value: string): void
}>()

const segments = computed(() => parseEffectLineRolls(props.line))

function pickKeyForSegmentIndex(segIndex: number): number {
  const segs = segments.value
  if (!segs) return 0
  let n = 0
  for (let i = 0; i < segIndex; i++) {
    if (segs[i]!.type === 'pick') n++
  }
  return n
}

function storageKey(segIndex: number): string {
  return `${props.pickKeyPrefix}#${pickKeyForSegmentIndex(segIndex)}`
}

function pickValue(segIndex: number): string {
  const segs = segments.value
  if (!segs || segs[segIndex]!.type !== 'pick') return ''
  const seg = segs[segIndex] as { type: 'pick'; options: string[] }
  const k = storageKey(segIndex)
  const cur = props.selections[k]
  if (cur !== undefined && seg.options.includes(cur)) return cur
  return seg.options[0] ?? ''
}

function onSelectChange(segIndex: number, value: string) {
  emit('set-pick', storageKey(segIndex), value)
}

watch(
  () => [props.line, props.pickKeyPrefix, props.selections] as const,
  () => {
    const segs = segments.value
    if (!segs) return
    let pi = 0
    for (const s of segs) {
      if (s.type !== 'pick') continue
      const k = `${props.pickKeyPrefix}#${pi}`
      const cur = props.selections[k]
      if (cur === undefined || !s.options.includes(cur)) {
        emit('set-pick', k, s.options[0]!)
      }
      pi++
    }
  },
  { immediate: true, deep: true }
)
</script>

<style scoped>
.equipment-effect-plain {
  white-space: pre-wrap;
  word-break: break-word;
}

.equipment-effect-line-roll {
  display: inline;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.55;
}

.equipment-effect-line-piece {
  white-space: pre-wrap;
}

.effect-roll-select {
  display: inline-block;
  vertical-align: baseline;
  margin: 0 2px;
  max-width: 5.5rem;
  padding: 2px 6px;
  border-radius: 6px;
  border: 1px solid rgba(233, 69, 96, 0.45);
  background: rgba(26, 26, 46, 0.95);
  color: rgba(255, 255, 255, 0.95);
  font-size: 11px;
  font-weight: 600;
  color-scheme: dark;
  cursor: pointer;
}

.effect-roll-select:focus-visible {
  outline: 2px solid rgba(233, 69, 96, 0.55);
  outline-offset: 1px;
}
</style>
