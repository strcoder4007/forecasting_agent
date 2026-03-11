<template>
  <div class="dashboard">
    <div class="page-header">
      <h2 class="page-title">Dashboard</h2>
      <p class="page-subtitle">Monitor your forecasting operations</p>
    </div>

    <!-- Stats Grid -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon validation">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
            <polyline points="22 4 12 14.01 9 11.01"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">Data Status</span>
          <span class="stat-value" :class="validationStatus">{{ validationStatus === 'ok' ? 'Valid' : 'Warning' }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon runs">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">Total Runs</span>
          <span class="stat-value">{{ totalRuns }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon completed">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">Completed</span>
          <span class="stat-value">{{ completedRuns }}</span>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon pending">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 2v4"/>
            <path d="M12 18v4"/>
            <path d="M4.93 4.93l2.83 2.83"/>
            <path d="M16.24 16.24l2.83 2.83"/>
            <path d="M2 12h4"/>
            <path d="M18 12h4"/>
            <path d="M4.93 19.07l2.83-2.83"/>
            <path d="M16.24 7.76l2.83-2.83"/>
          </svg>
        </div>
        <div class="stat-content">
          <span class="stat-label">In Progress</span>
          <span class="stat-value">{{ runningRuns }}</span>
        </div>
      </div>
    </div>

    <!-- Warnings -->
    <div v-if="warnings.length" class="warnings-card">
      <div class="warnings-header">
        <svg class="warning-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
          <line x1="12" y1="9" x2="12" y2="13"/>
          <line x1="12" y1="17" x2="12.01" y2="17"/>
        </svg>
        <span>Data Warnings</span>
      </div>
      <div class="warnings-list">
        <div v-for="w in warnings" :key="w" class="warning-item">
          {{ w }}
        </div>
      </div>
    </div>

    <div class="content-grid">
      <!-- Recent Runs -->
      <div class="card recent-runs">
        <div class="card-header">
          <h3 class="card-title">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            Recent Forecast Runs
          </h3>
          <router-link to="/history" class="view-all">View all</router-link>
        </div>
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <span>Loading...</span>
        </div>
        <div v-else-if="recentRuns.length === 0" class="empty-state">
          <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
          <p>No forecast runs yet</p>
          <router-link to="/run" class="btn btn-primary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Run a forecast
          </router-link>
        </div>
        <div v-else class="runs-list">
          <div v-for="run in recentRuns" :key="run.run_id" class="run-item">
            <div class="run-info">
              <div class="run-id">{{ run.run_id.substring(0, 8) }}</div>
              <div class="run-time">{{ formatDate(run.timestamp) }}</div>
            </div>
            <div class="status-badge" :class="run.status">
              <span class="status-dot"></span>
              {{ run.status }}
            </div>
          </div>
        </div>
      </div>

      <!-- Quick Actions -->
      <div class="card quick-actions">
        <div class="card-header">
          <h3 class="card-title">
            <svg class="card-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
            </svg>
            Quick Actions
          </h3>
        </div>
        <div class="actions-grid">
          <router-link to="/run" class="action-card">
            <div class="action-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="5 3 19 12 5 21 5 3"/>
              </svg>
            </div>
            <span>Run Forecast</span>
          </router-link>
          <router-link to="/results" class="action-card">
            <div class="action-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="18" y1="20" x2="18" y2="10"/>
                <line x1="12" y1="20" x2="12" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="14"/>
              </svg>
            </div>
            <span>View Results</span>
          </router-link>
          <router-link to="/history" class="action-card">
            <div class="action-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <circle cx="12" cy="12" r="10"/>
                <polyline points="12 6 12 12 16 14"/>
              </svg>
            </div>
            <span>History</span>
          </router-link>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Dashboard',
  data() {
    return {
      loading: true,
      validationStatus: 'unknown',
      warnings: [],
      recentRuns: []
    }
  },
  computed: {
    totalRuns() {
      return this.recentRuns.length
    },
    completedRuns() {
      return this.recentRuns.filter(r => r.status === 'completed').length
    },
    runningRuns() {
      return this.recentRuns.filter(r => r.status === 'running').length
    }
  },
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        const valRes = await axios.get('/api/data/validate')
        this.validationStatus = valRes.data.status
        this.warnings = valRes.data.warnings || []

        const histRes = await axios.get('/api/history')
        this.recentRuns = histRes.data.runs?.slice(0, 5) || []
      } catch (e) {
        console.error(e)
      }
      this.loading = false
    },
    formatDate(dateStr) {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-header {
  margin-bottom: 8px;
}

.page-title {
  font-family: 'Fira Code', monospace;
  font-size: 28px;
  font-weight: 700;
  color: #1E3A8A;
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: #64748B;
}

/* Stats Grid */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  transition: all 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon svg {
  width: 24px;
  height: 24px;
}

.stat-icon.validation {
  background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
  color: #065F46;
}

.stat-icon.runs {
  background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
  color: #1E40AF;
}

.stat-icon.completed {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  color: #92400E;
}

.stat-icon.pending {
  background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);
  color: #4338CA;
}

.stat-content {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 13px;
  color: #64748B;
  font-weight: 500;
}

.stat-value {
  font-family: 'Fira Code', monospace;
  font-size: 24px;
  font-weight: 700;
  color: #1E3A8A;
}

.stat-value.ok {
  color: #059669;
}

.stat-value.warning {
  color: #D97706;
}

/* Warnings */
.warnings-card {
  background: linear-gradient(135deg, #FEF3C7 0%, #FDE68A 100%);
  border: 1px solid #FCD34D;
  border-radius: 12px;
  padding: 16px 20px;
}

.warnings-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  color: #92400E;
  margin-bottom: 8px;
}

.warning-icon {
  width: 20px;
  height: 20px;
}

.warnings-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.warning-item {
  font-size: 14px;
  color: #B45309;
  padding-left: 28px;
}

/* Content Grid */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 360px;
  gap: 24px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.card-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #1E3A8A;
}

.card-icon {
  width: 20px;
  height: 20px;
  color: #3B82F6;
}

.view-all {
  font-size: 13px;
  color: #3B82F6;
  text-decoration: none;
  font-weight: 500;
}

.view-all:hover {
  text-decoration: underline;
}

/* Recent Runs */
.recent-runs {
  min-height: 300px;
}

.runs-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.run-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #F8FAFC;
  border-radius: 10px;
  transition: all 0.2s ease;
}

.run-item:hover {
  background: #F1F5F9;
}

.run-info {
  display: flex;
  align-items: center;
  gap: 16px;
}

.run-id {
  font-family: 'Fira Code', monospace;
  font-size: 14px;
  font-weight: 600;
  color: #3B82F6;
  background: #DBEAFE;
  padding: 4px 10px;
  border-radius: 6px;
}

.run-time {
  font-size: 13px;
  color: #64748B;
}

.status-badge {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}

.status-badge.completed, .status-badge.ok {
  background: #D1FAE5;
  color: #065F46;
}

.status-dot.completed, .status-dot.ok {
  background: #059669;
}

.status-badge.running {
  background: #FEF3C7;
  color: #92400E;
}

.status-dot.running {
  background: #D97706;
  animation: pulse 1.5s infinite;
}

.status-badge.failed {
  background: #FEE2E2;
  color: #991B1B;
}

.status-dot.failed {
  background: #DC2626;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Quick Actions */
.actions-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.action-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 20px 12px;
  background: #F8FAFC;
  border: 1px solid #E2E8F0;
  border-radius: 12px;
  text-decoration: none;
  color: #1E3A8A;
  font-size: 13px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.action-card:hover {
  background: #FFFFFF;
  border-color: #3B82F6;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.action-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.action-icon svg {
  width: 20px;
  height: 20px;
  color: #FFFFFF;
}

/* States */
.loading-state, .empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 40px 20px;
  color: #64748B;
}

.spinner {
  width: 32px;
  height: 32px;
  border: 3px solid #E2E8F0;
  border-top-color: #3B82F6;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: #94A3B8;
}

.empty-state p {
  font-size: 14px;
  margin-bottom: 8px;
}

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  
  .actions-grid {
    grid-template-columns: 1fr;
  }
}
</style>
