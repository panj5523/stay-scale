import { createRouter, createWebHistory } from 'vue-router'
import EnvironmentStatusView from '../views/EnvironmentStatusView.vue'
import ListingSearchView from '../views/ListingSearchView.vue'
import ManagementReviewView from '../views/ManagementReviewView.vue'
import RecommendationView from '../views/RecommendationView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'listing-search',
      component: ListingSearchView,
    },
    {
      path: '/recommendations',
      name: 'recommendations',
      component: RecommendationView,
    },
    {
      path: '/management/reviews',
      name: 'management-reviews',
      component: ManagementReviewView,
    },
    {
      path: '/status',
      name: 'environment-status',
      component: EnvironmentStatusView,
    },
  ],
})

export default router
