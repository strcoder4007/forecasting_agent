<template>
  <div class="results">
    <h2 class="page-title">Forecast Results</h2>

    <div v-if="loading" class="loading">Loading results...</div>

    <div v-else-if="error" class="error">
      {{ error }}
    </div>

    <div v-else>
      <!-- Controls -->
      <div class="controls">
        <div class="control-group">
          <label>Run ID:</label>
          <select v-model="selectedRunId" @change="loadResults" class="select">
            <option value="">Select a run</option>
            <option v-for="run in runs" :key="run.run_id" :value="run.run_id">
              {{ run.run_id.substring(0, 8) }} - {{ formatDate(run.timestamp) }}
            </option>
          </select>
        </div>
        <button @click="exportCSV" class="btn btn-secondary" :disabled="!results.length">
          Export CSV
        </button>
      </div>

      <!-- Stats -->
      <div v-if="results.length" class="stats">
        <div class="stat-card">
          <div class="stat-value">{{ results.length }}</div>
          <div class="stat-label">Total Combos</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ zeroForecasts }}</div>
          <div class="stat-label">Zero Forecasts</div>
        </div>
        <div class="stat-card">
          <div class="stat-value">{{ avgForecast }}</div>
          <div class="stat-label">Avg Forecast</div>
        </div>
      </div>

      <!-- Table -->
      <div v-if="results.length" class="table-container">
        <table class="data-table">
          <thead>
            <tr>
              <th>Store ID</th>
              <th>SKU ID</th>
              <th>Combo ID</th>
              <th>Forecast Week</th>
              <th>Forecast</th>
              <th>Lower 80%</th>
              <th>Upper 80%</th>
              <th>Model</th>
              <th>Segment</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, idx) in paginatedResults" :key="idx">
              <td>{{ row.store_id }}</td>
              <td class="sku">{{ row.sku_id?.substring(0, 20) }}...</td>
              <td class="combo">{{ row.combo_id?.substring(0, 25) }}...</td>
              <td>{{ row.forecast_week_start }}</td>
              <td class="forecast">{{ row.point_forecast }}</td>
              <td>{{ row.lower_80 }}</td>
              <td>{{ row.upper_80 }}</td>
              <td>{{ row.model_used }}</td>
              <td>
                <span class="segment-badge" :class="row.demand_segment">
                  {{ row.demand_segment }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>

        <!-- Pagination -->
        <div class="pagination">
          <button @click="page--" :disabled="page === 0" class="btn btn-secondary">
            Previous
          </button>
          <span class="page-info">Page {{ page + 1 }} of {{ totalPages }}</span>
          <button @click="page++" :disabled="page >= totalPages - 1" class="btn btn-secondary">
            Next
          </button>
        </div>
      </div>

      <div v-else class="empty">
        No results to display. <router-link to="/run">Run a forecast</router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'Results',
  data() {
    return {
      loading: true,
      error: null,
      runs: [],
      results: [],
      selectedRunId: '',
      page: 0,
      pageSize: 20
    }
  },
  computed: {
    paginatedResults() {
      const start = this.page * this.pageSize
      return this.results.slice(start, start + this.pageSize)
    },
    totalPages() {
      return Math.ceil(this.results.length / this.pageSize)
    },
    zeroForecasts() {
      return this.results.filter(r => r.is_zero_forecast === 1).length
    },
    avgForecast() {
      if (!this.results.length) return 0
      const total = this.results.reduce((sum, r) => sum + r.point_forecast, 0)
      return Math.round(total / this.results.length)
    }
  },
  async mounted() {
    await this.loadHistory()
    if (this.$route.params.runId) {
      this.selectedRunId = this.$route.params.runId
      await this.loadResults()
    }
  },
  methods: {
    async loadHistory() {
      try {
        const res = await axios.get('/api/history')
        this.runs = res.data.runs?.filter(r => r.status === 'completed') || []
      } catch (e) {
        console.error(e)
      }
      this.loading = false
    },
    async loadResults() {
      if (!this.selectedRunId) {
        this.results = []
        return
      }

      this.loading = true
      try {
        const res = await axios.get(`/api/forecast/results/${this.selectedRunId}`)
        this.results = res.data.rows || []
        this.page = 0
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      }
      this.loading = false
    },
    async exportCSV() {
      if (!this.selectedRunId) return
      window.open(`/api/export/${this.selectedRunId}`, '_blank')
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleString()
    }
  }
}
</script>

<style scoped>
.results {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.page-title {
  font-size: 24px;
  font-weight: 600;
  color: #1e293b;
}

.loading, .error, .empty {
  color: #64748B;
  font-size: 14px;
}

.error {
  color: #EF4444;
}

.controls {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-group label {
  font-size: 14px;
  color: #64748B;
}

.select {
  padding: 8px 12px;
  border: 1px solid #E2E8F0;
  border-radius: 6px;
  font-size: 14px;
  background: #FFFFFF;
  min-width: 300px;
}

.stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.stat-card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
}

.stat-value {
  font-size: 32px;
  font-weight: 600;
  color: #2563EB;
}

.stat-label {
  font-size: 14px;
  color: #64748B;
  margin-top: 4px;
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
  padding: 12px;
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

.data-table .sku,
.data-table .combo {
  font-family: monospace;
  font-size: 12px;
  color: #64748B;
}

.data-table .forecast {
  font-weight: 600;
  color: #2563EB;
}

.segment-badge {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 11px;
  font-weight: 500;
}

.segment-badge.smooth {
  background: #D1FAE5;
  color: #065F46;
}

.segment-badge.intermittent {
  background: #FEF3C7;
  color: #92400E;
}

.segment-badge.lumpy {
  background: #FEE2E2;
  color: #991B1B;
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-top: 1px solid #E2E8F0;
}

.page-info {
  font-size: 14px;
  color: #64748B;
}

.btn {
  display: inline-block;
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
}

.btn-secondary {
  background: #F1F5F9;
  color: #475569;
}

.btn-secondary:hover {
  background: #E2E8F0;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
