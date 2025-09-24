<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="text-center mb-8">
      <h2 class="text-3xl font-bold text-gray-900">Universal Data Sync Dashboard</h2>
      <p class="mt-2 text-lg text-gray-600">Monitor and manage your data synchronization workflows</p>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4 mb-8">
      <div v-for="stat in stats" :key="stat.label" class="bg-white overflow-hidden shadow rounded-lg">
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <div class="w-8 h-8 rounded-full flex items-center justify-center" :class="stat.iconBg">
                <span class="text-white text-sm font-bold">{{ stat.value }}</span>
              </div>
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">{{ stat.label }}</dt>
                <dd class="text-lg font-medium text-gray-900">{{ stat.value }}</dd>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="bg-white shadow rounded-lg mb-8">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Quick Actions</h3>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <router-link
            v-for="action in quickActions"
            :key="action.to"
            :to="action.to"
            class="relative block w-full p-4 border-2 border-gray-300 border-dashed rounded-lg text-center hover:border-gray-400 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 transition-colors"
          >
            <span class="text-3xl">{{ action.icon }}</span>
            <span class="mt-2 block text-sm font-medium text-gray-900">{{ action.label }}</span>
            <span class="block text-xs text-gray-500">{{ action.description }}</span>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Recent Activity -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">Recent Sync Activities</h3>
        <div class="flow-root">
          <ul class="-mb-8">
            <li v-for="(activity, index) in recentActivities" :key="activity.id">
              <div class="relative pb-8" :class="index !== recentActivities.length - 1 ? 'pb-8' : ''">
                <span v-if="index !== recentActivities.length - 1" class="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200" aria-hidden="true"></span>
                <div class="relative flex space-x-3">
                  <div>
                    <span class="h-8 w-8 rounded-full flex items-center justify-center ring-8 ring-white" :class="activity.iconBg">
                      <span class="text-sm">{{ activity.icon }}</span>
                    </span>
                  </div>
                  <div class="min-w-0 flex-1 pt-1.5 flex justify-between space-x-4">
                    <div>
                      <p class="text-sm text-gray-500">{{ activity.description }}</p>
                      <p class="text-xs text-gray-400">{{ activity.timestamp }}</p>
                    </div>
                    <div class="text-right text-sm whitespace-nowrap text-gray-500">
                      <Badge :variant="activity.status === 'Success' ? 'green' : activity.status === 'Failed' ? 'red' : 'yellow'">
                        {{ activity.status }}
                      </Badge>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Badge } from 'frappe-ui'

const stats = ref([
  { label: 'Active Chains', value: 12, iconBg: 'bg-blue-500' },
  { label: 'Successful Today', value: 347, iconBg: 'bg-green-500' },
  { label: 'Failed Today', value: 8, iconBg: 'bg-red-500' },
  { label: 'Avg Time (s)', value: 1.4, iconBg: 'bg-purple-500' }
])

const quickActions = ref([
  {
    to: '/wizard',
    icon: '🧙‍♂️',
    label: 'Setup Wizard',
    description: 'Create new sync chain'
  },
  {
    to: '/chains',
    icon: '⚙️',
    label: 'Manage Chains',
    description: 'View & edit existing chains'
  },
  {
    to: '/mapping',
    icon: '🔗',
    label: 'Field Mapping',
    description: 'Smart field mapping'
  },
  {
    to: '/logs',
    icon: '📋',
    label: 'Activity Logs',
    description: 'Monitor sync activities'
  }
])

const recentActivities = ref([
  {
    id: 1,
    icon: '🔄',
    description: 'Lead to Opportunity sync completed - 5 records synced',
    timestamp: '2 minutes ago',
    status: 'Success',
    iconBg: 'bg-green-500'
  },
  {
    id: 2,
    icon: '📝',
    description: 'Customer to Contact sync started - 3 records processing',
    timestamp: '5 minutes ago',
    status: 'Running',
    iconBg: 'bg-yellow-500'
  },
  {
    id: 3,
    icon: '⚠️',
    description: 'Employee sync failed - Permission denied error',
    timestamp: '10 minutes ago',
    status: 'Failed',
    iconBg: 'bg-red-500'
  }
])

onMounted(() => {
  // Load real data here
})
</script>