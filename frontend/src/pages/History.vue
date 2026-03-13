<template>
  <div class="history">
    <div class="page-header">
      <h2 class="page-title">History</h2>
      <p class="page-subtitle">Your past forecast runs</p>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>Loading...</span>
    </div>

    <div v-else-if="runs.length === 0" class="empty-state">
      <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <circle cx="12" cy="12" r="10"/>
        <polyline points="12 6 12 12 16 14"/>
      </svg>
      <h3>No forecasts yet</h3>
      <p>Run your first forecast to see it here</p>
      <router-link to="/run" class="btn btn-primary">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
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
          All Runs
        </h3>
        <span class="run-count">{{ runs.length }} {{ runs.length === 1 ? 'run' : 'runs' }}</span>
      </div>

      <div class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Run ID</th>
              <th>Date</th>
              <th>Status</th>
              <th>Combos</th>
              <th>WMAPE</th>
              <th>MAPE</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="run in runs" :key="run.run_id">
              <td class="run-id">{{ run.run_id.substring(0, 6) }}</td>
              <td class="date">{{ formatDate(run.timestamp) }}</td>
              <td>
                <span class="status-badge" :class="run.status">
                  <span class="status-dot"></span>
                  {{ run.status }}
                </span>
              </td>
              <td class="combos">{{ run.total_combos?.toLocaleString() || '-' }}</td>
              <td class="metric">{{ formatWMAPE(run.avg_wmape) }}</td>
              <td class="metric">{{ formatWMAPE(run.avg_mape) }}</td>
              <td>
                <div class="actions">
                  <router-link
                    v-if="run.status === 'completed'"
                    :to="'/run?id=' + run.run_id"
                    class="btn-icon"
                    title="View"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                      <circle cx="12" cy="12" r="3"/>
                    </svg>
                  </router-link>
                  <button @click="deleteRun(run.run_id)" class="btn-icon danger" title="Delete">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                      <polyline points="3 6 5 6 21 6"></polyline>
                      <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
                    </svg>
                  </button>
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
        hour: '2-digit', 
        minute: '2-digit'
      })
    },
    formatWMAPE(wmape) {
      if (!wmape) return '-'
      return (wmape * 100).toFixed(1) + '%'
    },
    async deleteRun(runId) {
      if (!confirm('Delete this run?')) return
      try {
        await axios.delete(`/api/history/${runId}`)
        await this.loadHistory()
      } catch (e) {
        console.error('Failed to delete run:', e)
      }
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
  font-size: 24px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 4px;
}

.page-subtitle {
  font-size: 14px;
  color: var(--color-text-muted);
}

/* Loading */
.loading-state {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px;
  color: var(--color-text-muted);
}

.spinner {
  width: 24px;
  height: 24px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
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
  padding: 60px 20px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  text-align: center;
}

.empty-icon {
  width: 48px;
  height: 48px;
  color: var(--color-text-muted);
}

.empty-state h3 {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
}

.empty-state p {
  font-size: 14px;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

/* Table */
.table-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.table-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
}

.table-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.table-icon {
  width: 18px;
  height: 18px;
  color: var(--color-primary);
}

.run-count {
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--color-bg);
  padding: 4px 10px;
  border-radius: 12px;
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
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--color-border);
}

.data-table th {
  background: var(--color-bg);
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.data-table tbody tr {
  transition: background 0.15s ease;
}

.data-table tbody tr:hover {
  background: rgba(124, 58, 237, 0.02);
}

.data-table td {
  font-size: 13px;
  color: var(--color-text);
}

.run-id {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: var(--color-primary);
}

.date {
  color: var(--color-text-muted);
}

.combos {
  font-family: 'Fira Code', monospace;
  color: var(--color-text-muted);
}

.metric {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: #10B981;
}

/* Status */
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
}

.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.status-badge.completed {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.status-dot.completed {
  background: #10B981;
}

.status-badge.running {
  background: rgba(245, 158, 11, 0.1);
  color: #D97706;
}

.status-dot.running {
  background: #F59E0B;
  animation: pulse 1.5s infinite;
}

.status-badge.failed {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
}

.status-dot.failed {
  background: #EF4444;
}

.status-badge.pending {
  background: var(--color-bg);
  color: var(--color-text-muted);
}

.status-dot.pending {
  background: var(--color-text-muted);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* Actions */
.actions {
  display: flex;
  gap: 6px;
}

.btn-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 6px;
  background: var(--color-bg);
  color: var(--color-text-muted);
  cursor: pointer;
  transition: var(--transition);
}

.btn-icon:hover {
  background: var(--color-border);
  color: var(--color-text);
}

.btn-icon.danger:hover {
  background: rgba(239, 68, 68, 0.1);
  color: #EF4444;
}

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: var(--radius-sm);
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  transition: var(--transition);
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: #6D28D9;
}
</style>
