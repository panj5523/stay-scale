import { createRouter, createWebHistory } from 'vue-router'
import { hasAdminSession } from '../auth/session'
import AdminLoginView from '../views/AdminLoginView.vue'
import ComparisonView from '../views/ComparisonView.vue'
import EnvironmentStatusView from '../views/EnvironmentStatusView.vue'
import ListingSearchView from '../views/ListingSearchView.vue'
import ManagementReviewView from '../views/ManagementReviewView.vue'
import OperationsDashboardView from '../views/OperationsDashboardView.vue'
import PlatformSyncView from '../views/PlatformSyncView.vue'
import RecommendationView from '../views/RecommendationView.vue'
import RestoreApprovalView from '../views/RestoreApprovalView.vue'
import UserAccountView from '../views/UserAccountView.vue'
import AIConversationView from '../views/AIConversationView.vue'

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
      path: '/account',
      name: 'user-account',
      component: UserAccountView,
    },
    { path: '/ai-companion', name: 'ai-companion', component: AIConversationView },
    {
      path: '/compare',
      name: 'comparison',
      component: ComparisonView,
    },
    {
      path: '/management/login',
      name: 'admin-login',
      component: AdminLoginView,
    },
    {
      path: '/management/dashboard',
      name: 'management-dashboard',
      component: OperationsDashboardView,
      meta: { requiresAdmin: true },
    },
    {
      path: '/management/reviews',
      name: 'management-reviews',
      component: ManagementReviewView,
      meta: { requiresAdmin: true },
    },
    {
      path: '/management/restore-requests',
      name: 'management-restore-requests',
      component: RestoreApprovalView,
      meta: { requiresAdmin: true },
    },
    {
      path: '/management/platform-sync',
      name: 'management-platform-sync',
      component: PlatformSyncView,
      meta: { requiresAdmin: true },
    },
    {
      path: '/status',
      name: 'environment-status',
      component: EnvironmentStatusView,
    },
  ],
})

router.beforeEach((to) => {
  if (to.meta.requiresAdmin && !hasAdminSession()) {
    return { name: 'admin-login', query: { redirect: to.fullPath } }
  }
  if (to.name === 'admin-login' && hasAdminSession()) {
    return { name: 'management-reviews' }
  }
})

export default router
