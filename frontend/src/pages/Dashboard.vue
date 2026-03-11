<template>
  <div class="dashboard">
    <h2 class="page-title">Dashboard</h2>

    <!-- Validation Status -->
    <div class="card">
      <h3 class="card-title">Data Validation</h3>
      <div v-if="loading" class="loading">Loading...</div>
      <div v-else>
        <div class="status-badge" :class="validationStatus">
          {{ validationStatus === 'ok' ? 'Valid' : 'Warning' }}
        </div>
        <div v-if="warnings.length" class="warnings">
          <div v-for="w in warnings" :key="w" class="warning-item">{{ w }}</div>
        </div>
      </div>
    </div>

    <!-- Recent Runs -->
    <div class="card">
      <h3 class="card-title">Recent Forecast Runs</h3>
      <div v-if="recentRuns.length === 0" class="empty">
        No forecast runs yet. <router-link to="/run">Run a forecast</router-link>
      </div>
      <div v-else class="runs-list">
        <div v-for="run in recentRuns" :key="run.run_id" class="run-item">
          <div class="run-info">
            <span class="run-id">{{ run.run_id.substring(0, 8) }}</span>
            <span class="run-time">{{ formatDate(run.timestamp) }}</span>
          </div>
          <div class="status-badge" :class="run.status">{{ run.status }}</div>
        </div>
      </div>
    </div>

    <!-- Quick Actions -->
    <div class="card">
      <h3 class="card-title">Quick Actions</h3>
      <div class="actions">
        <router-link to="/run" class="btn btn-primary">Run Forecast</router-link>
        <router-link to="/results" class="btn btn-secondary">View Results</router-link>
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
  async mounted() {
    await this.loadData()
  },
  methods: {
    async loadData() {
      this.loading = true
      try {
        // Validate data
        const valRes = await axios.get('/api/data/validate')
        this.validationStatus = valRes.data.status
        this.warnings = valRes.data.warnings || []

        // Get history
        const histRes = await axios.get('/api/history')
        this.recentRuns = histRes.data.runs?.slice(0, 5) || []
      } catch (e) {
        console.error(e)
      }
      this.loading = false
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString()
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

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}

.card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 24px;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 16px;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.ok, .status-badge.completed {
  background: #D1FAE5;
  color: #065F46;
}

.status-badge.warning, .status-badge.running {
  background: #FEF3C7;
  color: #92400E;
}

.status-badge.failed {
  background: #FEE2E2;
  color: #991B1B;
}

.warnings {
  margin-top: 12px;
}

.warning-item {
  font-size: 14px;
  color: #92400E;
  padding: 4px 0;
}

.loading, .empty {
  color: #64748B;
  font-size: 14px;
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
  padding: 12px;
  background: #F8FAFC;
  border-radius: 6px;
}

.run-info {
  display: flex;
  gap: 12px;
  align-items: center;
}

.run-id {
  font-family: monospace;
  font-size: 14px;
  color: #2563EB;
}

.run-time {
  font-size: 12px;
  color: #64748B;
}

.actions {
  display: flex;
  gap: 12px;
}

.btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-primary {
  background: #2563EB;
  color: #FFFFFF;
}

.btn-primary:hover {
  background: #1D4ED8;
}

.btn-secondary {
  background: #F1F5F9;
  color: #475569;
}

.btn-secondary:hover {
  background: #E2E8F0;
}
</style>
