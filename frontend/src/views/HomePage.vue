<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
    <!-- Hero Section -->
    <div class="relative overflow-hidden">
      <!-- Background Pattern -->
      <div class="absolute inset-0 opacity-5">
        <div class="absolute inset-0" style="background-image: url('data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%234F46E5' fill-opacity='0.1'%3E%3Ccircle cx='30' cy='30' r='2'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E');"></div>
      </div>

      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20">
        <!-- Header -->
        <div class="text-center mb-16">
          <div class="mb-8">
            <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg mb-6">
              <span class="text-3xl">🔧</span>
            </div>
            <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
              <span class="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent">
                Dev Assistant
              </span>
            </h1>
            <p class="text-xl md:text-2xl text-gray-600 max-w-3xl mx-auto leading-relaxed">
              Enterprise-grade developer productivity platform for
              <span class="font-semibold text-indigo-600">Frappe/ERPNext</span> systems
            </p>
          </div>

          <!-- Key Stats -->
          <div class="grid grid-cols-2 md:grid-cols-4 gap-6 max-w-4xl mx-auto mb-12">
            <div class="text-center">
              <div class="text-3xl font-bold text-blue-600">4+</div>
              <div class="text-sm text-gray-600">Core Features</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-green-600">90%+</div>
              <div class="text-sm text-gray-600">Field Mapping Accuracy</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-purple-600">100%</div>
              <div class="text-sm text-gray-600">Form Coverage</div>
            </div>
            <div class="text-center">
              <div class="text-3xl font-bold text-orange-600">5-Step</div>
              <div class="text-sm text-gray-600">Sync Wizard</div>
            </div>
          </div>

          <!-- CTA Buttons -->
          <div class="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <router-link
              to="/wizard"
              class="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              <span class="mr-2">🧙‍♂️</span>
              Start Sync Wizard
            </router-link>
            <router-link
              to="/dashboard"
              class="inline-flex items-center px-8 py-4 bg-white text-gray-700 font-semibold rounded-lg border-2 border-gray-300 hover:border-gray-400 hover:shadow-md transition-all duration-200"
            >
              <span class="mr-2">📊</span>
              View Dashboard
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Features Section -->
    <div class="py-20 bg-white">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-gray-900 mb-4">Powerful Features</h2>
          <p class="text-xl text-gray-600 max-w-3xl mx-auto">
            Everything you need to streamline your Frappe development workflow
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-8">
          <!-- Universal Data Sync -->
          <div class="group relative bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100 hover:shadow-lg transition-all duration-300">
            <div class="absolute top-4 right-4 text-2xl opacity-20">🔄</div>
            <div class="mb-6">
              <div class="w-12 h-12 bg-blue-600 rounded-lg flex items-center justify-center mb-4">
                <span class="text-white text-xl">🔄</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Universal Data Sync</h3>
              <p class="text-gray-600 mb-4">
                AI-powered synchronization system with smart field mapping and real-time processing
              </p>
            </div>

            <div class="space-y-3 mb-6">
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                5-step wizard interface for workflow creation
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Pre-built templates for common business processes
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Smart field mapping with 90%+ accuracy
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Real-time conflict resolution
              </div>
            </div>

            <router-link
              to="/wizard"
              class="inline-flex items-center text-blue-600 font-semibold hover:text-blue-800 transition-colors group-hover:translate-x-1 transform transition-transform"
            >
              Try Sync Wizard
              <span class="ml-2">→</span>
            </router-link>
          </div>

          <!-- Field Access Control -->
          <div class="group relative bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 border border-green-100 hover:shadow-lg transition-all duration-300">
            <div class="absolute top-4 right-4 text-2xl opacity-20">🔒</div>
            <div class="mb-6">
              <div class="w-12 h-12 bg-green-600 rounded-lg flex items-center justify-center mb-4">
                <span class="text-white text-xl">🔒</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Field Access Control</h3>
              <p class="text-gray-600 mb-4">
                Dynamic field-level security with role-based visibility and child table controls
              </p>
            </div>

            <div class="space-y-3 mb-6">
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Role-based field hiding and read-only controls
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Global application across all Frappe forms
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Child table button restrictions
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                User exception handling
              </div>
            </div>

            <a
              href="#"
              class="inline-flex items-center text-green-600 font-semibold hover:text-green-800 transition-colors group-hover:translate-x-1 transform transition-transform"
              @click.prevent="showComingSoon('Field Access Control')"
            >
              Configure Access Rules
              <span class="ml-2">→</span>
            </a>
          </div>

          <!-- Role Permission Management -->
          <div class="group relative bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-8 border border-purple-100 hover:shadow-lg transition-all duration-300">
            <div class="absolute top-4 right-4 text-2xl opacity-20">👥</div>
            <div class="mb-6">
              <div class="w-12 h-12 bg-purple-600 rounded-lg flex items-center justify-center mb-4">
                <span class="text-white text-xl">👥</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Role Management</h3>
              <p class="text-gray-600 mb-4">
                Bulk permission operations with validation and conflict resolution
              </p>
            </div>

            <div class="space-y-3 mb-6">
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Copy permissions between roles efficiently
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Overwrite control and duplicate handling
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Role existence validation
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Seamless Frappe integration
              </div>
            </div>

            <a
              href="#"
              class="inline-flex items-center text-purple-600 font-semibold hover:text-purple-800 transition-colors group-hover:translate-x-1 transform transition-transform"
              @click.prevent="showComingSoon('Role Management')"
            >
              Manage Roles
              <span class="ml-2">→</span>
            </a>
          </div>

          <!-- Modern Dashboard -->
          <div class="group relative bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-8 border border-orange-100 hover:shadow-lg transition-all duration-300">
            <div class="absolute top-4 right-4 text-2xl opacity-20">📊</div>
            <div class="mb-6">
              <div class="w-12 h-12 bg-orange-600 rounded-lg flex items-center justify-center mb-4">
                <span class="text-white text-xl">📊</span>
              </div>
              <h3 class="text-2xl font-bold text-gray-900 mb-2">Live Dashboard</h3>
              <p class="text-gray-600 mb-4">
                Real-time monitoring with responsive interface and activity tracking
              </p>
            </div>

            <div class="space-y-3 mb-6">
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Live sync statistics and metrics
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Quick action shortcuts
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Real-time activity stream
              </div>
              <div class="flex items-center text-sm text-gray-700">
                <span class="w-2 h-2 bg-green-500 rounded-full mr-3"></span>
                Mobile-optimized interface
              </div>
            </div>

            <router-link
              to="/dashboard"
              class="inline-flex items-center text-orange-600 font-semibold hover:text-orange-800 transition-colors group-hover:translate-x-1 transform transition-transform"
            >
              View Dashboard
              <span class="ml-2">→</span>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Quick Start Section -->
    <div class="py-20 bg-gray-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-16">
          <h2 class="text-4xl font-bold text-gray-900 mb-4">Get Started in Minutes</h2>
          <p class="text-xl text-gray-600 max-w-3xl mx-auto">
            Follow these simple steps to start using Dev Assistant
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div class="text-center">
            <div class="w-16 h-16 bg-blue-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <span class="text-white text-2xl font-bold">1</span>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Choose Your Workflow</h3>
            <p class="text-gray-600">
              Select from pre-built templates or create a custom sync process using our wizard
            </p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-green-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <span class="text-white text-2xl font-bold">2</span>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Map Your Fields</h3>
            <p class="text-gray-600">
              Use AI-powered smart mapping to connect fields between DocTypes with 90%+ accuracy
            </p>
          </div>

          <div class="text-center">
            <div class="w-16 h-16 bg-purple-600 rounded-full flex items-center justify-center mx-auto mb-6">
              <span class="text-white text-2xl font-bold">3</span>
            </div>
            <h3 class="text-xl font-semibold text-gray-900 mb-4">Activate & Monitor</h3>
            <p class="text-gray-600">
              Launch your sync chain and monitor real-time performance through the dashboard
            </p>
          </div>
        </div>

        <div class="text-center mt-12">
          <router-link
            to="/wizard"
            class="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
          >
            <span class="mr-2">🚀</span>
            Launch Wizard Now
          </router-link>
        </div>
      </div>
    </div>

    <!-- Navigation Links Section -->
    <div class="py-16 bg-white border-t border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">Explore All Features</h2>
          <p class="text-lg text-gray-600">
            Access all Dev Assistant capabilities from these dedicated interfaces
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <router-link
            to="/dashboard"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
              <span class="text-2xl">📊</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Dashboard</h3>
            <p class="text-sm text-gray-600 mb-4">Live statistics and activity monitoring</p>
            <div class="flex items-center text-blue-600 text-sm font-medium">
              View Dashboard
              <span class="ml-2 group-hover:translate-x-1 transform transition-transform">→</span>
            </div>
          </router-link>

          <router-link
            to="/wizard"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-green-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
              <span class="text-2xl">🧙‍♂️</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Sync Wizard</h3>
            <p class="text-sm text-gray-600 mb-4">Create workflows in 5 easy steps</p>
            <div class="flex items-center text-green-600 text-sm font-medium">
              Start Wizard
              <span class="ml-2 group-hover:translate-x-1 transform transition-transform">→</span>
            </div>
          </router-link>

          <router-link
            to="/chains"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
              <span class="text-2xl">⚙️</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Manage Chains</h3>
            <p class="text-sm text-gray-600 mb-4">View and edit existing sync chains</p>
            <div class="flex items-center text-purple-600 text-sm font-medium">
              Manage Chains
              <span class="ml-2 group-hover:translate-x-1 transform transition-transform">→</span>
            </div>
          </router-link>

          <router-link
            to="/logs"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-orange-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-orange-200 transition-colors">
              <span class="text-2xl">📋</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Activity Logs</h3>
            <p class="text-sm text-gray-600 mb-4">Monitor sync activities and troubleshoot</p>
            <div class="flex items-center text-orange-600 text-sm font-medium">
              View Logs
              <span class="ml-2 group-hover:translate-x-1 transform transition-transform">→</span>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <!-- Footer -->
    <div class="bg-gray-900 text-white py-12">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center">
          <div class="inline-flex items-center justify-center w-12 h-12 bg-blue-600 rounded-lg mb-6">
            <span class="text-xl">🔧</span>
          </div>
          <h3 class="text-2xl font-bold mb-4">Dev Assistant</h3>
          <p class="text-gray-400 max-w-2xl mx-auto mb-8">
            Enterprise-grade developer productivity platform for Frappe/ERPNext systems.
            Streamline your development workflow with intelligent automation.
          </p>
          <div class="text-sm text-gray-500">
            Built with ❤️ for the Frappe community
          </div>
        </div>
      </div>
    </div>

    <!-- Coming Soon Modal -->
    <div v-if="showModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity" @click="showModal = false"></div>
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="text-center">
              <div class="text-4xl mb-4">🚧</div>
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-2">{{ modalFeature }}</h3>
              <p class="text-sm text-gray-500">This feature is under development and will be available soon!</p>
            </div>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="showModal = false"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-blue-600 text-base font-medium text-white hover:bg-blue-700 focus:outline-none sm:ml-3 sm:w-auto sm:text-sm"
            >
              Got it!
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const showModal = ref(false)
const modalFeature = ref('')

const showComingSoon = (feature) => {
  modalFeature.value = feature
  showModal.value = true
}
</script>

<style scoped>
/* Custom animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.fade-in-up {
  animation: fadeInUp 0.6s ease-out;
}

/* Gradient text support for older browsers */
.bg-clip-text {
  -webkit-background-clip: text;
  background-clip: text;
}

/* Hover effects */
.group:hover .group-hover\:translate-x-1 {
  transform: translateX(0.25rem);
}

.group:hover .group-hover\:bg-blue-200 {
  background-color: rgb(191 219 254);
}

.group:hover .group-hover\:bg-green-200 {
  background-color: rgb(187 247 208);
}

.group:hover .group-hover\:bg-purple-200 {
  background-color: rgb(221 214 254);
}

.group:hover .group-hover\:bg-orange-200 {
  background-color: rgb(254 215 170);
}
</style>