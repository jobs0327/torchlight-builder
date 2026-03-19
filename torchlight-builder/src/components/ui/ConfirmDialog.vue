<template>
  <Teleport to="body">
    <div v-if="modelValue" class="dialog-overlay" @click.self="onCancel">
      <div class="dialog-panel" role="dialog" aria-modal="true">
        <div class="dialog-header">
          <div class="dialog-title">{{ title }}</div>
        </div>

        <div class="dialog-body">
          <div class="dialog-message">{{ message }}</div>
        </div>

        <div class="dialog-footer">
          <button class="btn btn-secondary" type="button" @click="onCancel">
            {{ cancelText }}
          </button>
          <button class="btn btn-primary" type="button" @click="onConfirm">
            {{ confirmText }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
type Props = {
  modelValue: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
}

const props = withDefaults(defineProps<Props>(), {
  title: '确认操作',
  confirmText: '确认',
  cancelText: '取消'
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm'): void
  (e: 'cancel'): void
}>()

function onCancel() {
  emit('update:modelValue', false)
  emit('cancel')
}

function onConfirm() {
  emit('update:modelValue', false)
  emit('confirm')
}
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.65);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.dialog-panel {
  width: min(420px, calc(100vw - 32px));
  background: rgba(15, 15, 26, 0.98);
  border: 1px solid rgba(255, 255, 255, 0.12);
  border-radius: 12px;
  box-shadow: 0 20px 80px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.dialog-header {
  padding: 12px 14px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
}

.dialog-title {
  font-size: 14px;
  color: #e5e7eb;
  font-weight: 700;
}

.dialog-body {
  padding: 14px;
}

.dialog-message {
  font-size: 13px;
  color: rgba(229, 231, 235, 0.9);
  line-height: 1.5;
  white-space: pre-wrap;
}

.dialog-footer {
  padding: 12px 14px;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.btn {
  border: 1px solid rgba(255, 255, 255, 0.14);
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.06);
  color: #e5e7eb;
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.1);
}

.btn-primary {
  background: rgba(250, 204, 21, 0.18);
  border-color: rgba(250, 204, 21, 0.35);
  color: #facc15;
}

.btn-primary:hover {
  background: rgba(250, 204, 21, 0.26);
}
</style>

