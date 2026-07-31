import { createRouter, createWebHistory } from 'vue-router'
import EnvironmentStatusView from '../views/EnvironmentStatusView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'environment-status',
      component: EnvironmentStatusView,
    },
  ],
})

export default router
