<template>
  <div class="h-full">
    <!-- Loading State -->
    <div v-if="loading" class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
      <div class="text-center">
        <!-- Modern Animated Loader -->
        <div class="relative mb-8">
          <!-- Outer rotating ring -->
          <div class="w-20 h-20 mx-auto relative">
            <div class="absolute inset-0 rounded-full border-4 border-blue-200"></div>
            <div class="absolute inset-0 rounded-full border-4 border-transparent border-t-blue-600 animate-spin"></div>
          </div>

          <!-- Center sync icon -->
          <div class="absolute inset-0 flex items-center justify-center">
            <div class="w-8 h-8 bg-white rounded-full shadow-lg flex items-center justify-center animate-pulse">
              <svg class="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path>
              </svg>
            </div>
          </div>
        </div>

        <!-- Loading text with typing animation -->
        <div class="space-y-2">
          <h3 class="text-xl font-semibold text-gray-800 animate-fadeIn">
            🔧 Dev Assistant
          </h3>
          <div class="flex items-center justify-center space-x-1">
            <span class="text-gray-600">Loading</span>
            <div class="flex space-x-1">
              <div class="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 0ms"></div>
              <div class="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 150ms"></div>
              <div class="w-1 h-1 bg-blue-600 rounded-full animate-bounce" style="animation-delay: 300ms"></div>
            </div>
          </div>

          <!-- Progress indication -->
          <div class="mt-4 w-48 mx-auto bg-gray-200 rounded-full h-1">
            <div class="bg-gradient-to-r from-blue-500 to-indigo-600 h-1 rounded-full animate-pulse" style="width: 75%"></div>
          </div>

          <p class="text-sm text-gray-500 mt-2 animate-fadeIn" style="animation-delay: 500ms">
            Loading your productivity platform...
          </p>
        </div>
      </div>
    </div>

    <!-- Main App -->
    <div v-else class="min-h-screen">
      <!-- Navigation -->
      <nav class="bg-white shadow-sm border-b border-gray-200">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div class="flex justify-between h-16">
            <div class="flex items-center">
              <div class="flex-shrink-0 flex items-center">
                <h1 class="text-xl font-bold text-gray-900">🔄 Universal Data Sync</h1>
              </div>
              <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                <router-link
                  v-for="link in navLinks"
                  :key="link.to"
                  :to="link.to"
                  class="border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300 inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-colors"
                  :class="{ 'border-indigo-500 text-indigo-600': $route.path === link.to }"
                >
                  {{ link.icon }} {{ link.label }}
                </router-link>
              </div>
            </div>
            <div class="flex items-center space-x-4">
              <div class="text-sm text-gray-500">
                Welcome, {{ user?.full_name || 'User' }}
              </div>
            </div>
          </div>
        </div>
      </nav>

      <!-- Main Content -->
      <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
// Removed LoadingIndicator import - using custom loader

const loading = ref(true)
const user = ref(null)

const navLinks = [
  { to: '/', label: 'Home', icon: '🏠' },
  { to: '/dashboard', label: 'Dashboard', icon: '📊' },
  { to: '/wizard', label: 'Setup Wizard', icon: '🧙‍♂️' },
  { to: '/chains', label: 'Manage Chains', icon: '⚙️' },
  { to: '/mapping', label: 'Field Mapping', icon: '🔗' },
  { to: '/logs', label: 'Activity Logs', icon: '📋' }
]

onMounted(async () => {
  // Get user info from Frappe
  if (window.frappe?.session?.user_info) {
    user.value = window.frappe.session.user_info
  }

  // Simulate loading
  setTimeout(() => {
    loading.value = false
  }, 1000)
})
</script>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.6s ease-out forwards;
}

/* Enhanced bounce animation for dots */
@keyframes bounceDots {
  0%, 80%, 100% {
    transform: scale(0.8);
    opacity: 0.5;
  }
  40% {
    transform: scale(1.2);
    opacity: 1;
  }
}

.animate-bounce {
  animation: bounceDots 1.4s infinite ease-in-out both;
}
</style>