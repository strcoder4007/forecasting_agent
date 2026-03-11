<template>
  <div class="history">
    <h2 class="page-title">Forecast History</h2>

    <div v-if="loading" class="loading">Loading history...</div>

    <div v-else-if="runs.length === 0" class="empty">
      No forecast runs yet. <router-link to="/run">Run a forecast</router-link>
    </div>

    <div v-else class="table-container">
      <table class="data-table">
        <thead>
          <tr>
            <th>Run ID</th>
            <th>Timestamp</th>
            <th>Status</th>
            <th>Total Combos</th>
            <th>Avg WMAPE</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="run in runs" :key="run.run_id">
            <td class="run-id">{{ run.run_id.substring(0, 8) }}</td>
            <td>{{ formatDate(run.timestamp) }}</td>
            <td>
              <span class="status-badge" :class="run.status">
                {{ run.status }}
              </span>
            </td>
            <td>{{ run.total_combos }}</td>
            <td>{{ formatWMAPE(run.avg_wmape) }}</td>
            <td>
              <div class="actions">
                <router-link
                  v-if="run.status === 'completed'"
                  :to="'/results/' + run.run_id"
                  class="btn btn-secondary"
                >
                  View
                </router-link>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
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
      return new Date(dateStr).toLocaleString()
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

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}

.loading, .empty {
  color: #64748B;
  font-size: 14px;
}

.table-container {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid #E2E8F0;
}

.data-table th {
  background: #F8FAFC;
  font-size: 12px;
  font-weight: 600;
  color: #64748B;
  text-transform: uppercase;
}

.data-table td {
  font-size: 14px;
  color: #1e293b;
}

.run-id {
  font-family: monospace;
  color: #2563EB;
}

.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 16px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.completed {
  background: #D1FAE5;
  color: #065F46;
}

.status-badge.running {
  background: #FEF3C7;
  color: #92400E;
}

.status-badge.failed {
  background: #FEE2E2;
  color: #991B1B;
}

.status-badge.pending {
  background: #F1F5F9;
  color: #64748B;
}

.actions {
  display: flex;
  gap: 8px;
}

.btn {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 13px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
}

.btn-secondary {
  background: #F1F5F9;
  color: #475569;
}

.btn-secondary:hover {
  background: #E2E8F0;
}
</style>
