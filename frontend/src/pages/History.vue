<template>
  <div class="history">
    <div class="page-header">
      <h2 class="page-title">Forecast History</h2>
      <p class="page-subtitle">View all your past forecast runs</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading history...</span>
    </div>

    <div v-else-if="runs.length === 0" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
      <h3>No forecasts yet</h3>
      <p>Run your first forecast to see it here</p>
      <router-link to="/run" class="btn btn-primary">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <polygon points="5 3 19 12 5 21 5 3"/>
        </svg>
        Run Forecast
      </router-link>
    </div>

    <div v-else class="table-card">
      <div class="table-header">
        <h3 class="table-title">
          <svg class="table-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <polyline points="12 6 12 12 16 14"/>
          </svg>
          All Forecast Runs
        </h3>
        <span class="run-count">{{ runs.length }} runs</span>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Date & Time</th>
              <th>Status</th>
              <th>Combos</th>
              <th>Avg WMAPE</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.run_id">
              <td class="run-id">{{ run.run_id.substring(0, 8) }}</td>
              <td class="date">{{ formatDate(run.timestamp) }}</td>
              <td>
                <span class="status-badge" :class="run.status">
                  <span class="status-dot"></span>
                  {{ run.status }}
                </span>
              </td>
              <td class="combos">{{ run.total_combos?.toLocaleString() || '-' }}</td>
              <td class="wmape">{{ formatWMAPE(run.avg_wmape) }}</td>
              <td>
                <div class="actions">
                  <router-link
                    v-if="run.status === 'completed'"
                    :to="'/results/' + run.run_id"
                    class="btn btn-secondary btn-sm"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                    View
                  </router-link>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'History',
  data() {
    return {
      loading: true,
      runs: []
    }
  },
  async mounted() {
    await this.loadHistory()
  },
  methods: {
    async loadHistory() {
      try {
        const res = await axios.get('/api/history')
        this.runs = res.data.runs || []
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
        year: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
      })
    },
    formatWMAPE(wmape) {
      if (!wmape) return '-'
      return (wmape * 100).toFixed(2) + '%'
    }
  }
}
</script>

<style scoped>
.history {
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

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
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

/* Empty */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 80px 20px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  text-align: center;
}

.empty-icon {
  width: 64px;
  height: 64px;
  color: #94A3B8;
}

.empty-state h3 {
  font-size: 18px;
  font-weight: 600;
  color: #1E3A8A;
}

.empty-state p {
  font-size: 14px;
  color: #64748B;
  margin-bottom: 8px;
}

/* Table */
.table-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid #E2E8F0;
}

.table-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 16px;
  font-weight: 600;
  color: #1E3A8A;
}

.table-icon {
  width: 20px;
  height: 20px;
  color: #3B82F6;
}

.run-count {
  font-size: 13px;
  color: #64748B;
  background: #F1F5F9;
  padding: 6px 12px;
  border-radius: 20px;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 14px 16px;
  text-align: left;
  border-bottom: 1px solid #F1F5F9;
}

.data-table th {
  background: #F8FAFC;
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table tbody tr {
  transition: background 0.15s ease;
}

.data-table tbody tr:hover {
  background: #F8FAFC;
}

.data-table td {
  font-size: 14px;
  color: #1E3A8A;
}

.run-id {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: #3B82F6;
}

.date {
  color: #64748B;
}

.combos {
  font-family: 'Fira Code', monospace;
}

.wmape {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: #059669;
}

/* Status */
.status-badge {
  display: inline-flex;
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

.status-badge.completed {
  background: #D1FAE5;
  color: #065F46;
}

.status-dot.completed {
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

.status-badge.pending {
  background: #F1F5F9;
  color: #64748B;
}

.status-dot.pending {
  background: #94A3B8;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Actions */
.actions {
  display: flex;
  gap: 8px;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: all 0.2s ease;
  border: none;
  cursor: pointer;
}

.btn-secondary {
  background: #F1F5F9;
  color: #1E3A8A;
}

.btn-secondary:hover {
  background: #E2E8F0;
}

.btn-primary {
  background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
  color: #FFFFFF;
  box-shadow: 0 4px 12px rgba(245, 158, 11, 0.3);
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
}

.btn-sm {
  padding: 8px 12px;
  font-size: 12px;
}
</style>
