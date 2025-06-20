import { createRouter, createWebHistory, RouteRecordRaw } from 'vue-router'
import UnitListView from '@/views/UnitListView.vue'

const routes: Array<RouteRecordRaw> = [
  {
    path: '/',
    name: 'Home',
    component: UnitListView,
  },
  // Add more routes as needed
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

export default router
