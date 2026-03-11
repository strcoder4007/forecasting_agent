import { createRouter, createWebHistory } from 'vue-router'
import Dashboard from './pages/Dashboard.vue'
import RunForecast from './pages/RunForecast.vue'
import Results from './pages/Results.vue'
import History from './pages/History.vue'

const routes = [
  { path: '/', name: 'Dashboard', component: Dashboard },
  { path: '/run', name: 'RunForecast', component: RunForecast },
  { path: '/results/:runId?', name: 'Results', component: Results },
  { path: '/history', name: 'History', component: History },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
