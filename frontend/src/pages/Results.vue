<template>
  <div class="results">
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">Forecast Results</h2>
        <p class="page-subtitle">View and export your forecasting outputs</p>
      </div>
    </div>

    <div v-if="loading && !results.length" class="loading-state">
      <div class="spinner"></div>
      <span>Loading results...</span>
    </div>

    <div v-else-if="error" class="error-card">
      <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <circle cx="12" cy="12" r="10"/>
        <line x1="15" y1="9" x2="9" y2="15"/>
        <line x1="9" y1="9" x2="15" y2="15"/>
      </svg>
      <span>{{ error }}</span>
    </div>

    <div v-else>
      <!-- Controls -->
      <div class="controls-card">
        <div class="control-group">
          <label class="control-label">Select Run</label>
          <div class="select-wrapper">
            <select v-model="selectedRunId" @change="loadResults" class="select">
              <option value="">Choose a forecast run...</option>
              <option v-for="run in runs" :key="run.run_id" :value="run.run_id">
                {{ run.run_id.substring(0, 8) }} - {{ formatDate(run.timestamp) }}
              </option>
            </select>
            <svg class="select-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <polyline points="6 9 12 15 18 9"/>
            </svg>
          </div>
        </div>
        <button @click="exportCSV" class="btn btn-secondary" :disabled="!results.length">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
            <polyline points="7 10 12 15 17 10"/>
            <line x1="12" y1="15" x2="12" y2="3"/>
          </svg>
          Export CSV
        </button>
        <button @click="deleteRun" class="btn btn-danger" :disabled="!selectedRunId">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polyline points="3 6 5 6 21 6"/>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
            <line x1="10" y1="11" x2="10" y2="17"/>
            <line x1="14" y1="11" x2="14" y2="17"/>
          </svg>
          Delete
        </button>
      </div>

      <!-- Stats -->
      <div v-if="results.length" class="stats-grid">
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
              <line x1="3" y1="9" x2="21" y2="9"/>
              <line x1="9" y1="21" x2="9" y2="9"/>
            </svg>
            <span class="stat-label">Total Combos</span>
          </div>
          <div class="stat-value">{{ results.length.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon zero" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <line x1="4.93" y1="4.93" x2="19.07" y2="19.07"/>
            </svg>
            <span class="stat-label">Zero Forecasts</span>
          </div>
          <div class="stat-value">{{ zeroForecasts.toLocaleString() }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon avg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="12" y1="20" x2="12" y2="10"/>
              <line x1="18" y1="20" x2="18" y2="4"/>
              <line x1="6" y1="20" x2="6" y2="16"/>
            </svg>
            <span class="stat-label">Avg Forecast</span>
          </div>
          <div class="stat-value">{{ avgForecast }}</div>
        </div>
        <div class="stat-card">
          <div class="stat-header">
            <svg class="stat-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
            </svg>
            <span class="stat-label">Model</span>
          </div>
          <div class="stat-value model">{{ modelUsed }}</div>
        </div>
      </div>

      <!-- Table -->
      <div v-if="results.length" class="table-card">
        <div class="table-header">
          <h3 class="table-title">Forecast Data</h3>
          <div class="table-info">
            Showing {{ paginatedResults.length }} of {{ results.length }} results
          </div>
        </div>
        
        <div class="table-container">
          <table class="data-table">
            <thead>
              <tr>
                <th>Store</th>
                <th>SKU</th>
                <th>Forecast</th>
                <th>Lower 80%</th>
                <th>Upper 80%</th>
                <th>Segment</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(row, idx) in paginatedResults" :key="idx">
                <td class="store-id">{{ row.store_id }}</td>
                <td class="sku" :title="row.sku_id">{{ truncate(row.sku_id, 25) }}</td>
                <td class="forecast">{{ row.point_forecast }}</td>
                <td class="ci">{{ row.lower_80 }}</td>
                <td class="ci">{{ row.upper_80 }}</td>
                <td>
                  <span class="segment-badge" :class="row.demand_segment">
                    {{ row.demand_segment }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination -->
        <div class="pagination">
          <button @click="page--" :disabled="page === 0" class="btn btn-secondary btn-sm">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <polyline points="15 18 9 12 15 6"/>
            </svg>
            Previous
          </button>
          <div class="page-info">
            <span class="page-number">{{ page + 1 }}</span>
            <span class="page-divider">of</span>
            <span class="page-number">{{ totalPages }}</span>
          </div>
          <button @click="page++" :disabled="page >= totalPages - 1" class="btn btn-secondary btn-sm">
            Next
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
              <polyline points="9 18 15 12 9 6"/>
            </svg>
          </button>
        </div>
      </div>

      <div v-else class="empty-state">
        <svg class="empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
          <line x1="12" y1="22.08" x2="12" y2="12"/>
        </svg>
        <h3>No results to display</h3>
        <p>Run a forecast to see results here</p>
        <router-link to="/run" class="btn btn-primary">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <polygon points="5 3 19 12 5 21 5 3"/>
          </svg>
          Run Forecast
        </router-link>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { saveResults, getResults } from '../utils/db'

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
      pageSize: 25
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
    },
    modelUsed() {
      if (!this.results.length) return '-'
      return this.results[0].model_used?.replace('_blend', '') || '-'
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
      this.error = null
      try {
        let rows = await getResults(this.selectedRunId)
        if (!rows) {
          const res = await axios.get(`/api/forecast/results/${this.selectedRunId}`)
          rows = res.data.rows || []
          if (rows.length > 0) {
            await saveResults(this.selectedRunId, rows)
          }
        }
        this.results = rows
        this.page = 0
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      }
      this.loading = false
    },
    async exportCSV() {
      if (!this.results || !this.results.length) return
      
      const keys = Object.keys(this.results[0])
      let csvContent = keys.join(',') + '\n'
      
      this.results.forEach(row => {
        csvContent += keys.map(k => {
          let val = row[k] === null || row[k] === undefined ? '' : row[k]
          // wrap string in quotes if it contains commas
          if (typeof val === 'string' && val.includes(',')) {
            val = `"${val}"`
          }
          return val
        }).join(',') + '\n'
      })
      
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      const url = URL.createObjectURL(blob)
      link.setAttribute('href', url)
      link.setAttribute('download', `forecast_${this.selectedRunId}.csv`)
      link.style.visibility = 'hidden'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    },
    async deleteRun() {
      if (!this.selectedRunId) return
      
      if (!confirm('Are you sure you want to delete this forecast run? This action cannot be undone.')) {
        return
      }
      
      try {
        await axios.delete(`/api/history/${this.selectedRunId}`)
        this.results = []
        this.selectedRunId = ''
        await this.loadHistory()
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      }
    },
    formatDate(dateStr) {
      return new Date(dateStr).toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric',
        hour: '2-digit', 
        minute: '2-digit'
      })
    },
    truncate(str, len) {
      if (!str) return ''
      return str.length > len ? str.substring(0, len) + '...' : str
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

/* Loading & Error */
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

.error-card {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: #FEE2E2;
  border: 1px solid #FECACA;
  border-radius: 12px;
  color: #991B1B;
  font-size: 14px;
}

.error-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}

/* Controls */
.controls-card {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 20px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-label {
  font-size: 13px;
  font-weight: 500;
  color: #64748B;
}

.select-wrapper {
  position: relative;
}

.select {
  appearance: none;
  padding: 12px 40px 12px 16px;
  border: 1px solid #E2E8F0;
  border-radius: 10px;
  font-size: 14px;
  background: #FFFFFF;
  min-width: 320px;
  color: #1E3A8A;
  cursor: pointer;
  transition: all 0.2s ease;
}

.select:focus {
  outline: none;
  border-color: #3B82F6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.select-icon {
  position: absolute;
  right: 14px;
  top: 50%;
  transform: translateY(-50%);
  width: 18px;
  height: 18px;
  color: #64748B;
  pointer-events: none;
}

/* Stats */
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
}

.stat-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.stat-icon {
  width: 20px;
  height: 20px;
  color: #3B82F6;
}

.stat-icon.zero {
  color: #DC2626;
}

.stat-icon.avg {
  color: #059669;
}

.stat-label {
  font-size: 13px;
  color: #64748B;
  font-weight: 500;
}

.stat-value {
  font-family: 'Fira Code', monospace;
  font-size: 28px;
  font-weight: 700;
  color: #1E3A8A;
}

.stat-value.model {
  font-size: 18px;
  text-transform: capitalize;
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
  font-size: 16px;
  font-weight: 600;
  color: #1E3A8A;
}

.table-info {
  font-size: 13px;
  color: #64748B;
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

.store-id {
  font-family: 'Fira Code', monospace;
  font-weight: 500;
  color: #3B82F6;
}

.sku {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: #64748B;
  max-width: 200px;
}

.forecast {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: #059669;
}

.ci {
  font-family: 'Fira Code', monospace;
  color: #64748B;
}

.segment-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 600;
  text-transform: capitalize;
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

/* Pagination */
.pagination {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
  padding: 16px 24px;
  border-top: 1px solid #F1F5F9;
}

.page-info {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  color: #64748B;
}

.page-number {
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  color: #1E3A8A;
}

.page-divider {
  color: #94A3B8;
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

/* Buttons */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  border-radius: 10px;
  font-size: 14px;
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

.btn-secondary:hover:not(:disabled) {
  background: #E2E8F0;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
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
  padding: 8px 16px;
  font-size: 13px;
}

/* Responsive */
@media (max-width: 1024px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .controls-card {
    flex-direction: column;
    align-items: stretch;
  }
  
  .select {
    min-width: 100%;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
