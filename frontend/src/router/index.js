export const routes = [
  {
    path: '/',
    name: 'HomePage',
    component: () => import('../views/HomePage.vue')
  },
  {
    path: '/dev-assistant-homepage',
    name: 'DevAssistantHomePage',
    component: () => import('../views/SimpleHomePage.vue')
  },
  {
    path: '/universal-sync',
    name: 'UniversalSync',
    component: () => import('../views/HomePage.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('../views/Dashboard.vue')
  },
  {
    path: '/wizard',
    name: 'SyncWizard',
    component: () => import('../views/SyncWizard.vue')
  },
  {
    path: '/chains',
    name: 'ManageChains',
    component: () => import('../views/ManageChains.vue')
  },
  {
    path: '/mapping',
    name: 'FieldMapping',
    component: () => import('../views/FieldMapping.vue')
  },
  {
    path: '/logs',
    name: 'ActivityLogs',
    component: () => import('../views/ActivityLogs.vue')
  }
]