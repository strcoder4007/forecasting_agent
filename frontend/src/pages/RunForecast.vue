<template>
  <div class="run-forecast">
    <div class="page-header">
      <h2 class="page-title">Run Forecast</h2>
      <p class="page-subtitle">Execute the demand forecasting pipeline</p>
    </div>

    <div class="grid-layout">
      <!-- Main Card -->
      <div class="card main-card">
        <div class="card-header">
          <div class="card-title-section">
            <div class="card-icon-wrapper">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
              </svg>
            </div>
            <div>
              <h3 class="card-title">Start New Forecast</h3>
              <p class="card-description">Run demand forecasting for all SKU-store combinations</p>
            </div>
          </div>
        </div>

        <div v-if="!running" class="action-area">
          <button @click="startForecast" class="btn btn-primary btn-lg">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
              <polygon points="5 3 19 12 5 21 5 3"/>
            </svg>
            Start Forecast
          </button>
          <p class="action-note">This will process ~48,000 store-SKU combinations</p>
        </div>

        <!-- Running State -->
        <div v-else class="running-area">
          <div class="progress-card">
            <div class="progress-header">
              <span class="progress-label">Progress</span>
              <span class="progress-value">{{ progress }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progress + '%' }">
                <div class="progress-glow"></div>
              </div>
            </div>
          </div>

          <div class="stage-card">
            <div class="stage-item">
              <span class="stage-label">Current Stage</span>
              <span class="stage-value">{{ formatStage(stage) }}</span>
            </div>
            <div class="stage-item">
              <span class="stage-label">Status</span>
              <span class="stage-status running">
                <span class="status-pulse"></span>
                Processing...
              </span>
            </div>
          </div>

          <div class="logs-card">
            <div class="logs-header">Execution Logs</div>
            <div class="logs-container" ref="logsContainer">
              <div v-if="logs.length === 0" class="log-line empty">Waiting for logs...</div>
              <div v-for="(log, idx) in logs" :key="idx" class="log-line">
                <span class="log-text">{{ log }}</span>
              </div>
            </div>
          </div>

          <button @click="checkStatus" class="btn btn-secondary">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <polyline points="23 4 23 10 17 10"/>
              <polyline points="1 20 1 14 7 14"/>
              <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
            </svg>
            Refresh Status
          </button>
        </div>

        <!-- Error -->
        <div v-if="error" class="error-card">
          <svg class="error-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
          <div class="error-content">
            <span class="error-title">Forecast Failed</span>
            <span class="error-message">{{ error }}</span>
          </div>
        </div>
      </div>

      <!-- Sidebar -->
      <div class="sidebar">
        <!-- Current Run -->
        <div v-if="currentRunId" class="card current-run">
          <h3 class="card-title-sm">Current Run</h3>
          <div class="run-id-badge">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            {{ currentRunId.substring(0, 8) }}
          </div>
          <router-link :to="'/results/' + currentRunId" class="btn btn-secondary btn-full">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
              <circle cx="12" cy="12" r="3"/>
            </svg>
            View Results
          </router-link>
        </div>

        <!-- Info Card -->
        <div class="card info-card">
          <h3 class="card-title-sm">Pipeline Details</h3>
          <div class="info-list">
            <div class="info-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
                <line x1="3" y1="9" x2="21" y2="9"/>
                <line x1="9" y1="21" x2="9" y2="9"/>
              </svg>
              <span>48,000 combos</span>
            </div>
            <div class="info-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <line x1="12" y1="20" x2="12" y2="10"/>
                <line x1="18" y1="20" x2="18" y2="4"/>
                <line x1="6" y1="20" x2="6" y2="16"/>
              </svg>
              <span>LightGBM + Ridge</span>
            </div>
            <div class="info-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>
              </svg>
              <span>Weekly aggregation</span>
            </div>
            <div class="info-item">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
                <polyline points="14 2 14 8 20 8"/>
              </svg>
              <span>False-zero correction</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'RunForecast',
  data() {
    return {
      running: false,
      currentRunId: null,
      progress: 0,
      stage: '',
      message: '',
      error: null,
      pollInterval: null,
      logs: []
    }
  },
  beforeUnmount() {
    if (this.pollInterval) {
      clearInterval(this.pollInterval)
    }
  },
  methods: {
    async startForecast() {
      this.error = null
      try {
        const res = await axios.post('/api/forecast/run')
        this.currentRunId = res.data.run_id
        this.running = true
        this.progress = 0
        this.stage = 'starting'
        this.message = 'Forecast started...'
        this.logs = []

        this.pollInterval = setInterval(() => this.checkStatus(), 2000)
      } catch (e) {
        this.error = e.response?.data?.detail || e.message
      }
    },
    async checkStatus() {
      if (!this.currentRunId) return

      try {
        const res = await axios.get(`/api/forecast/status/${this.currentRunId}`)
        const data = res.data

        this.progress = data.progress
        this.stage = data.stage
        this.message = data.message
        this.logs = data.logs || []
        
        this.$nextTick(() => {
          if (this.$refs.logsContainer) {
            this.$refs.logsContainer.scrollTop = this.$refs.logsContainer.scrollHeight
          }
        })

        if (data.status === 'completed') {
          this.running = false
          clearInterval(this.pollInterval)
          this.$router.push(`/results/${this.currentRunId}`)
        } else if (data.status === 'failed') {
          this.running = false
          this.error = data.message
          clearInterval(this.pollInterval)
        }
      } catch (e) {
        console.error(e)
      }
    },
    formatStage(stage) {
      const stageMap = {
        'starting': 'Initializing',
        'loading_data': 'Loading Data',
        'aggregating': 'Aggregating',
        'correcting': 'Correcting',
        'segmenting': 'Segmenting',
        'features': 'Engineering Features',
        'training': 'Training Models',
        'predicting': 'Generating Forecasts',
        'done': 'Complete'
      }
      return stageMap[stage] || stage
    }
  }
}
</script>

<style scoped>
.run-forecast {
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

/* Logs */
.logs-card {
  margin-top: 24px;
  background: #0f172a;
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #1e293b;
  display: flex;
  flex-direction: column;
}

.logs-header {
  background: #1e293b;
  color: #94a3b8;
  padding: 8px 16px;
  font-size: 12px;
  font-family: 'Fira Code', monospace;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  border-bottom: 1px solid #334155;
}

.logs-container {
  padding: 16px;
  max-height: 250px;
  overflow-y: auto;
  font-family: 'Fira Code', monospace;
  font-size: 13px;
  color: #a5b4fc;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-line {
  line-height: 1.4;
  word-break: break-all;
}

.log-line.empty {
  color: #64748b;
  font-style: italic;
}

.log-text {
  color: #e2e8f0;
}

.grid-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 24px;
}

/* Main Card */
.main-card {
  padding: 0;
}

.card-header {
  padding: 24px;
  border-bottom: 1px solid #F1F5F9;
}

.card-title-section {
  display: flex;
  align-items: flex-start;
  gap: 16px;
}

.card-icon-wrapper {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(135deg, #1E40AF 0%, #3B82F6 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.card-icon-wrapper svg {
  width: 24px;
  height: 24px;
  color: #FFFFFF;
}

.card-title {
  font-size: 18px;
  font-weight: 600;
  color: #1E3A8A;
  margin-bottom: 4px;
}

.card-description {
  font-size: 14px;
  color: #64748B;
}

/* Action Area */
.action-area {
  padding: 32px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.action-note {
  font-size: 13px;
  color: #94A3B8;
}

/* Running Area */
.running-area {
  padding: 24px;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.progress-card {
  background: #F8FAFC;
  border-radius: 12px;
  padding: 16px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-label {
  font-size: 13px;
  color: #64748B;
  font-weight: 500;
}

.progress-value {
  font-family: 'Fira Code', monospace;
  font-size: 18px;
  font-weight: 700;
  color: #3B82F6;
}

.progress-bar {
  height: 8px;
  background: #E2E8F0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3B82F6 0%, #1E40AF 100%);
  border-radius: 4px;
  transition: width 0.3s ease;
  position: relative;
}

.progress-glow {
  position: absolute;
  top: 0;
  right: 0;
  width: 40px;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.3));
  animation: glow 1.5s ease-in-out infinite;
}

@keyframes glow {
  0%, 100% { opacity: 0; }
  50% { opacity: 1; }
}

.stage-card {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stage-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.stage-label {
  font-size: 12px;
  color: #64748B;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.stage-value {
  font-size: 14px;
  font-weight: 600;
  color: #1E3A8A;
}

.stage-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
  font-weight: 600;
  color: #D97706;
}

.status-pulse {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #D97706;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.9); }
}

/* Error */
.error-card {
  margin: 0 24px 24px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 16px;
  background: #FEE2E2;
  border: 1px solid #FECACA;
  border-radius: 12px;
}

.error-icon {
  width: 24px;
  height: 24px;
  color: #DC2626;
  flex-shrink: 0;
}

.error-content {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.error-title {
  font-size: 14px;
  font-weight: 600;
  color: #991B1B;
}

.error-message {
  font-size: 13px;
  color: #B91C1C;
}

/* Sidebar */
.sidebar {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.card {
  background: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 20px;
}

.card-title-sm {
  font-size: 14px;
  font-weight: 600;
  color: #1E3A8A;
  margin-bottom: 16px;
}

/* Current Run */
.current-run .run-id-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Fira Code', monospace;
  font-size: 16px;
  font-weight: 600;
  color: #3B82F6;
  background: #DBEAFE;
  padding: 10px 14px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.current-run .run-id-badge svg {
  width: 16px;
  height: 16px;
}

/* Info Card */
.info-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: #64748B;
}

.info-item svg {
  width: 16px;
  height: 16px;
  color: #94A3B8;
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

.btn-lg {
  padding: 16px 32px;
  font-size: 16px;
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

.btn-secondary {
  background: #F1F5F9;
  color: #1E3A8A;
}

.btn-secondary:hover {
  background: #E2E8F0;
}

.btn-full {
  width: 100%;
}

/* Responsive */
@media (max-width: 1024px) {
  .grid-layout {
    grid-template-columns: 1fr;
  }
  
  .sidebar {
    flex-direction: row;
  }
  
  .sidebar .card {
    flex: 1;
  }
}

@media (max-width: 640px) {
  .sidebar {
    flex-direction: column;
  }
  
  .stage-card {
    grid-template-columns: 1fr;
  }
}
</style>
