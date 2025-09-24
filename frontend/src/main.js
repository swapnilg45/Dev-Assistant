import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import SimpleApp from './SimpleApp.vue'
import './index.css'

// Import routes
import { routes } from './router/index.js'

// Create router
const router = createRouter({
  history: createWebHistory('/universal-sync'),
  routes
})

// Create app
const app = createApp(SimpleApp)

// Use router only - remove Frappe UI dependency
app.use(router)

// Mount app
app.mount('#app')