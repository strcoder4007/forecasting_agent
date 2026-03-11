<template>
  <div class="run-forecast">
    <h2 class="page-title">Run Forecast</h2>

    <div class="card">
      <h3 class="card-title">Start New Forecast</h3>
      <p class="description">
        Run the demand forecasting pipeline to generate SKU-store demand predictions.
        This process will aggregate data, train models, and generate forecasts.
      </p>

      <div v-if="!running" class="action-area">
        <button @click="startForecast" class="btn btn-primary">
          Start Forecast
        </button>
      </div>

      <!-- Running State -->
      <div v-else class="running-area">
        <div class="progress-container">
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <span class="progress-text">{{ progress }}%</span>
        </div>
        <div class="stage-info">
          <span class="stage-label">Stage:</span>
          <span class="stage-name">{{ stage }}</span>
        </div>
        <div class="message">{{ message }}</div>
        <button @click="checkStatus" class="btn btn-secondary">
          Refresh Status
        </button>
      </div>

      <!-- Error -->
      <div v-if="error" class="error-area">
        <div class="error-message">{{ error }}</div>
      </div>
    </div>

    <!-- Current Run Info -->
    <div v-if="currentRunId" class="card">
      <h3 class="card-title">Current Run</h3>
      <div class="run-info">
        <span class="run-id">Run ID: {{ currentRunId.substring(0, 8) }}</span>
        <router-link :to="'/results/' + currentRunId" class="btn btn-secondary">
          View Results
        </router-link>
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
      pollInterval: null
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

        // Start polling
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
  margin-bottom: 12px;
}

.description {
  color: #64748B;
  font-size: 14px;
  margin-bottom: 24px;
}

.action-area {
  padding: 20px 0;
}

.btn {
  display: inline-block;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  text-decoration: none;
  transition: all 0.2s;
  border: none;
  cursor: pointer;
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

.running-area {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.progress-container {
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  flex: 1;
  height: 8px;
  background: #E2E8F0;
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: #2563EB;
  transition: width 0.3s ease;
}

.progress-text {
  font-size: 14px;
  font-weight: 500;
  color: #2563EB;
  min-width: 40px;
}

.stage-info {
  display: flex;
  gap: 8px;
}

.stage-label {
  font-size: 14px;
  color: #64748B;
}

.stage-name {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
}

.message {
  font-size: 14px;
  color: #64748B;
}

.error-area {
  margin-top: 16px;
  padding: 12px;
  background: #FEE2E2;
  border-radius: 6px;
}

.error-message {
  color: #991B1B;
  font-size: 14px;
}

.run-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.run-id {
  font-family: monospace;
  font-size: 14px;
  color: #64748B;
}
</style>
