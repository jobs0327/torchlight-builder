<template>
  <Teleport to="body">
    <div v-if="visible" class="toast-wrap">
      <div class="toast" :class="type">
        <div class="toast-text">{{ message }}</div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed } from 'vue'

type Props = {
  message: string
  type?: 'info' | 'warning' | 'error' | 'success'
}

const props = withDefaults(defineProps<Props>(), {
  type: 'warning'
})

const visible = computed(() => (props.message || '').trim().length > 0)
</script>

<style scoped>
.toast-wrap {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 10000;
  pointer-events: none;
}

.toast {
  pointer-events: auto;
  min-width: 260px;
  max-width: min(520px, calc(100vw - 32px));
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.12);
  background: rgba(15, 15, 26, 0.96);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.55);
  backdrop-filter: blur(6px);
}

.toast.warning {
  border-color: rgba(250, 204, 21, 0.35);
}

.toast.error {
  border-color: rgba(233, 69, 96, 0.55);
}

.toast.success {
  border-color: rgba(74, 222, 128, 0.45);
}

.toast-text {
  color: rgba(229, 231, 235, 0.92);
  font-size: 13px;
  line-height: 1.4;
}
</style>

