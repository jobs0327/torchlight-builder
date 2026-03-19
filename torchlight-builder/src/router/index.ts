import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/views/Home.vue')
  },
  {
    path: '/talent',
    name: 'Talent',
    component: () => import('@/views/Talent.vue')
  },
  {
    path: '/skills',
    name: 'Skills',
    component: () => import('@/views/Skills.vue')
  },
  {
    path: '/equipment',
    name: 'Equipment',
    component: () => import('@/views/Equipment.vue')
  },
  {
    path: '/hero',
    name: 'Hero',
    component: () => import('@/views/Hero.vue')
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
