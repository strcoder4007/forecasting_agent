import { createRouter, createWebHistory } from 'vue-router'
import RunForecast from './pages/RunForecast.vue'
import History from './pages/History.vue'

const routes = [
  { path: '/', redirect: '/run' },
  { path: '/run', name: 'RunForecast', component: RunForecast },
  { path: '/history', name: 'History', component: History },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
