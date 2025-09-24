<template>
  <div class="px-4 py-6 sm:px-0">
    <div class="text-center mb-8">
      <h2 class="text-2xl font-bold text-gray-900">📋 Activity Logs</h2>
      <p class="mt-2 text-gray-600">Real-time sync monitoring and troubleshooting</p>
    </div>

    <div class="text-center py-12">
      <div class="text-6xl mb-4">🚧</div>
      <h3 class="text-xl font-medium text-gray-900 mb-2">Coming Soon</h3>
      <p class="text-gray-600 mb-4">Activity monitoring features are under development</p>
      <router-link to="/">
        <Button>Back to Dashboard</Button>
      </router-link>
    </div>
  </div>
</template>

<script setup>
import { Button } from 'frappe-ui'
</script>