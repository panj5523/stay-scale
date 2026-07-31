import { createRouter, createWebHistory } from 'vue-router'
import EnvironmentStatusView from '../views/EnvironmentStatusView.vue'
import ListingSearchView from '../views/ListingSearchView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'listing-search',
      component: ListingSearchView,
    },
    {
      path: '/status',
      name: 'environment-status',
      component: EnvironmentStatusView,
    },
  ],
})

export default router
