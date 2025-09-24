<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
    <!-- Hero Section -->
    <div class="relative overflow-hidden">
      <div class="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-16 pb-20">
        <!-- Header -->
        <div class="text-center mb-16">
          <div class="mb-8">
            <div class="inline-flex items-center justify-center w-20 h-20 bg-gradient-to-br from-blue-600 to-indigo-700 rounded-2xl shadow-lg mb-6">
              <span class="text-3xl">🔧</span>
            </div>
            <h1 class="text-5xl md:text-6xl font-bold text-gray-900 mb-4">
              <span style="background: linear-gradient(to right, #2563eb, #4f46e5); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
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
            <a
              href="/universal-sync"
              class="inline-flex items-center px-8 py-4 bg-gradient-to-r from-blue-600 to-indigo-600 text-white font-semibold rounded-lg shadow-lg hover:shadow-xl transform hover:scale-105 transition-all duration-200"
            >
              <span class="mr-2">🔄</span>
              Universal Sync
            </a>
            <a
              href="#dashboard"
              class="inline-flex items-center px-8 py-4 bg-white text-gray-700 font-semibold rounded-lg border-2 border-gray-300 hover:border-gray-400 hover:shadow-md transition-all duration-200"
            >
              <span class="mr-2">📊</span>
              View Dashboard
            </a>
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

        <div class="grid grid-cols-1 md:grid-cols-2 gap-8">
          <!-- Universal Data Sync -->
          <div class="group relative bg-gradient-to-br from-blue-50 to-indigo-50 rounded-2xl p-8 border border-blue-100 hover:shadow-lg transition-all duration-300">
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
            <a
              href="/universal-sync"
              class="inline-flex items-center text-blue-600 font-semibold hover:text-blue-800 transition-colors"
            >
              Try Sync System
              <span class="ml-2">→</span>
            </a>
          </div>

          <!-- Field Access Control -->
          <div class="group relative bg-gradient-to-br from-green-50 to-emerald-50 rounded-2xl p-8 border border-green-100 hover:shadow-lg transition-all duration-300">
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
              href="#coming-soon"
              class="inline-flex items-center text-green-600 font-semibold hover:text-green-800 transition-colors"
            >
              Configure Access Rules
              <span class="ml-2">→</span>
            </a>
          </div>

          <!-- Role Permission Management -->
          <div class="group relative bg-gradient-to-br from-purple-50 to-violet-50 rounded-2xl p-8 border border-purple-100 hover:shadow-lg transition-all duration-300">
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
              href="#coming-soon"
              class="inline-flex items-center text-purple-600 font-semibold hover:text-purple-800 transition-colors"
            >
              Manage Roles
              <span class="ml-2">→</span>
            </a>
          </div>

          <!-- Live Dashboard -->
          <div class="group relative bg-gradient-to-br from-orange-50 to-red-50 rounded-2xl p-8 border border-orange-100 hover:shadow-lg transition-all duration-300">
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
            <a
              href="#dashboard"
              class="inline-flex items-center text-orange-600 font-semibold hover:text-orange-800 transition-colors"
            >
              View Dashboard
              <span class="ml-2">→</span>
            </a>
          </div>
        </div>
      </div>
    </div>

    <!-- Navigation Links Section -->
    <div class="py-16 bg-gray-50 border-t border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="text-center mb-12">
          <h2 class="text-3xl font-bold text-gray-900 mb-4">Explore All Features</h2>
          <p class="text-lg text-gray-600">
            Access all Dev Assistant capabilities from these dedicated interfaces
          </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <a
            href="#dashboard"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-blue-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-blue-200 transition-colors">
              <span class="text-2xl">📊</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Dashboard</h3>
            <p class="text-sm text-gray-600 mb-4">Live statistics and activity monitoring</p>
            <div class="flex items-center text-blue-600 text-sm font-medium">
              View Dashboard
              <span class="ml-2">→</span>
            </div>
          </a>

          <a
            href="/universal-sync"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-green-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-green-200 transition-colors">
              <span class="text-2xl">🔄</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Universal Sync</h3>
            <p class="text-sm text-gray-600 mb-4">Complete data synchronization platform</p>
            <div class="flex items-center text-green-600 text-sm font-medium">
              Start Syncing
              <span class="ml-2">→</span>
            </div>
          </a>

          <a
            href="#coming-soon"
            class="group bg-white p-6 rounded-xl border border-gray-200 hover:border-purple-300 hover:shadow-md transition-all duration-200"
          >
            <div class="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center mb-4 group-hover:bg-purple-200 transition-colors">
              <span class="text-2xl">🚀</span>
            </div>
            <h3 class="font-semibold text-gray-900 mb-2">Advanced Features</h3>
            <p class="text-sm text-gray-600 mb-4">Field access control, role management & more</p>
            <div class="flex items-center text-purple-600 text-sm font-medium">
              Coming Soon
              <span class="ml-2">→</span>
            </div>
          </a>
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
  </div>
</template>

<script setup>
// No external dependencies - pure Vue 3
</script>

<style scoped>
/* Custom hover effects */
.group:hover .group-hover\:translate-x-1 {
  transform: translateX(0.25rem);
}
</style>