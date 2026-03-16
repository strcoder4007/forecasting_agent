<template>
  <div class="workspace-wrapper">
    <div class="chat-page">
      <div class="chat-container">
        <!-- Chat Area -->
        <div class="chat-messages" ref="chatHistory">
          <div v-if="messages.length === 0" class="welcome-state">
            <div class="welcome-header">
              <div class="welcome-icon">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="28" height="28">
                  <path d="M3 3v18h18"></path>
                  <path d="M18 9l-5 5-4-4-3 3"></path>
                </svg>
              </div>
              <div>
                <h2>Forecasting Assistant</h2>
                <p>Ask me about demand forecasts, inventory risks, or run a new forecast.</p>
              </div>
            </div>

            <div class="suggestion-cards">
              <div class="card">
                <div class="card-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>
                  </svg>
                  <span>Demand Forecasting</span>
                </div>
                <button @click="sendQuick('What is the forecasted demand for next week?')">Forecasted demand next week</button>
                <button @click="sendQuick('Which 10 stores are expected to sell the most next week?')">Top stores next week</button>
                <button @click="sendQuick('Show me SKUs forecasted to sell more than 100 units')">High-demand SKUs</button>
              </div>

              <div class="card">
                <div class="card-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
                    <line x1="12" y1="9" x2="12" y2="13"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  <span>Inventory Risks</span>
                </div>
                <button @click="sendQuick('Which products are at risk of stockout?')">Products at stockout risk</button>
                <button @click="sendQuick('Which products have 0 forecast due to being out of stock?')">Zero forecast - out of stock</button>
                <button @click="sendQuick('Are there smooth demand items currently out of stock?')">Smooth demand out of stock</button>
              </div>

              <div class="card">
                <div class="card-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <circle cx="12" cy="12" r="10"/>
                    <path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"/>
                    <line x1="12" y1="17" x2="12.01" y2="17"/>
                  </svg>
                  <span>Insights</span>
                </div>
                <button @click="sendQuick('Break down forecasted sales by store grade')">Sales by store grade</button>
                <button @click="sendQuick('Which region has highest lumpy demand?')">Lumpy demand by region</button>
                <button @click="sendQuick('How accurate is the forecast overall?')">Forecast accuracy</button>
              </div>

              <div class="card card-action">
                <div class="card-header">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                    <polygon points="5 3 19 12 5 21 5 3"/>
                  </svg>
                  <span>Run Forecast</span>
                </div>
                <button @click="sendQuick('Run a new forecast for me')" class="primary">Run new forecast</button>
                <p class="card-hint">Process your data and get predictions</p>
              </div>
            </div>
          </div>

          <template v-for="(msg, idx) in messages" :key="idx">
            <div
              v-if="!msg.hidden"
              class="message"
              :class="msg.role"
            >
              <div v-if="msg.role === 'ai'" class="avatar">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                  <circle cx="12" cy="12" r="10"></circle>
                  <path d="M12 16v-4"></path>
                  <path d="M12 8h.01"></path>
                </svg>
              </div>
              
              <div class="message-content">
                <div class="text" v-html="formatMessage(msg.content)"></div>
              </div>
            </div>
          </template>

          <!-- Inline Thinking Indicator -->
          <div v-if="loading" class="message ai">
            <div class="avatar loading-avatar">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 16v-4"></path>
                <path d="M12 8h.01"></path>
              </svg>
            </div>
            <div class="message-content inline-thinking">
              <span class="dot"></span><span class="dot"></span><span class="dot"></span>
            </div>
          </div>
        </div>

        <div class="input-area">
          <textarea 
            ref="chatInput"
            v-model="query" 
            @keydown.enter.exact.prevent="sendMessage"
            @input="adjustTextarea"
            placeholder="Ask something or run a forecast..." 
            :disabled="loading || forecasting"
            rows="1"
          ></textarea>
          <button v-if="!forecasting" @click="sendMessage" :disabled="!query.trim() || loading" class="send-btn" :class="{ 'pulse': loading }">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <line x1="22" y1="2" x2="11" y2="13"></line>
              <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
            </svg>
          </button>
          <button v-else @click="cancelForecast" class="cancel-btn" title="Stop Forecast">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <rect x="6" y="6" width="12" height="12"></rect>
            </svg>
          </button>
        </div>
      </div>
    </div>

    <!-- Agent Activity Right Panel -->
    <AgentActivity 
      :currentRunId="currentRunId"
      :trace="currentTrace"
      :pipelineStage="pipelineStage"
      :pipelineStatus="pipelineStatus"
      @clear="clearTrace"
    />
  </div>
</template>


<script>
import axios from 'axios'
import { marked } from 'marked'
import { saveResults, getResults } from '../utils/db'
import AgentActivity from '../components/AgentActivity.vue'

export default {
  name: 'RunForecast',
  components: { AgentActivity },
  data() {
    return {
      query: '',
      messages: [],
      loading: false,
      forecasting: false,
      currentRunId: null,
      pollInterval: null,
      currentTrace: [],
      forecastLogCount: 0,
      forecastTraceCount: 0,
      pipelineStage: '',
      pipelineStatus: 'idle'
    }
  },
  async mounted() {
    if (this.$route.query.id) {
      this.currentRunId = this.$route.query.id;
      this.currentTrace = [];
      this.pipelineStatus = 'completed';
      this.pipelineStage = 'done';
      await this.loadResultsIfMissing();
      // Fetch traces for the historical run
      await this.loadTracesForRun(this.currentRunId);
    }
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval)
  },
  methods: {
    adjustTextarea(e) {
      const el = e.target;
      el.style.height = 'auto';
      el.style.height = (el.scrollHeight) + 'px';
      if (el.value === '') {
        el.style.height = 'auto';
      }
    },
    formatMessage(text) {
      return marked(text)
    },
    formatArgs(args) {
      return JSON.stringify(args, null, 2)
    },
    sendQuick(text) {
      this.query = text
      this.sendMessage()
    },
    clearRunContext() {
      this.currentRunId = null;
      this.pipelineStatus = 'idle';
      this.pipelineStage = '';
      if (this.$route.query.id) {
        this.$router.replace({ query: {} })
      }
    },
    async sendMessage(overrideText = null, isHidden = false) {
      if (!overrideText && (!this.query.trim() || this.loading || this.forecasting)) return

      const userText = overrideText || this.query.trim()
      if (!overrideText) {
        this.query = ''
        this.$nextTick(() => { if (this.$refs.chatInput) this.$refs.chatInput.style.height = 'auto' })
      }

      this.messages.push({ 
        role: 'user', 
        type: 'text', 
        content: userText,
        hidden: isHidden 
      })
      this.loading = true      

      
      this.scrollToBottom()

      try {
        const payload = { 
          messages: this.messages.filter(m => m.type === 'text').map(m => ({
            role: m.role,
            content: m.content
          }))
        }
        
        if (this.currentRunId) {
          payload.run_id = this.currentRunId
        }
        
        const res = await axios.post(`/api/chat`, payload)
        
        // Remove 'thinking' state
        
        
        if (res.data.trace && res.data.trace.length > 0) {
          // Append new trace items
          this.currentTrace.push(...res.data.trace)
          this.$nextTick(() => {
            const el = this.$refs.traceBody
            if (el) el.scrollTop = el.scrollHeight
          })
        }
        
        if (res.data.action === 'START_FORECAST') {
          this.messages.push({ role: 'ai', type: 'text', content: res.data.response })
          await this.startForecast()
        } else if (res.data.action === 'LOAD_RUN') {
           this.messages.push({ role: 'ai', type: 'text', content: res.data.response })
           this.currentRunId = res.data.action_payload
           this.$router.replace({ query: { id: this.currentRunId } })
           await this.loadResultsIfMissing()
        } else {
          this.messages.push({ role: 'ai', type: 'text', content: res.data.response })
        }
      } catch (e) {
        this.messages.push({ role: 'ai', type: 'text', content: `**Error:** ${e.response?.data?.detail || e.message}` })
      } finally {
        this.loading = false
        this.$nextTick(() => { this.$refs.chatInput?.focus() })
        this.scrollToBottom()
      }
    },
    clearTrace() {
      this.currentTrace = [];
    },
    async startForecast() {
      this.forecasting = true
      this.forecastLogCount = 0
      this.forecastTraceCount = 0
      try {
        const res = await axios.post('/api/forecast/run')
        this.currentRunId = res.data.run_id

        this.pipelineStatus = 'running'
        this.pipelineStage = 'starting'
        this.pollInterval = setInterval(() => this.checkForecastStatus(), 1500)
        this.$router.replace({ query: { id: this.currentRunId } })

      } catch (e) {
        this.pipelineStatus = 'failed'
        this.forecasting = false
      }
    },
    async cancelForecast() {
      if (!this.currentRunId) return;
      try {
        await axios.post(`/api/forecast/cancel/${this.currentRunId}`);
        this.forecasting = false;
        clearInterval(this.pollInterval);
        this.pipelineStatus = 'idle';
        this.pipelineStage = '';
        this.currentTrace.push({
          type: 'error',
          agent: 'system',
          name: 'Status',
          message: 'Forecast cancelled by user.'
        });
        this.currentRunId = null;
        this.$router.replace({ query: {} });
      } catch (e) {
        console.error("Failed to cancel forecast:", e);
      }
    },    async checkForecastStatus() {
      if (!this.currentRunId) return
      try {
        const res = await axios.get(`/api/forecast/status/${this.currentRunId}`)
        const data = res.data
        
        let hasNewTraces = false;
        
        if (data.traces && data.traces.length > this.forecastTraceCount) {
          const newTraces = data.traces.slice(this.forecastTraceCount)
          this.currentTrace.push(...newTraces)
          this.forecastTraceCount = data.traces.length
          hasNewTraces = true;
        }
        
        if (data.logs && data.logs.length > this.forecastLogCount) {
          const newLogs = data.logs.slice(this.forecastLogCount)
          newLogs.forEach(log => {
            this.currentTrace.push({
              type: 'info',
              agent: 'system',
              name: 'Pipeline',
              message: log
            })
            hasNewTraces = true;
          })
          this.forecastLogCount = data.logs.length
        }
        
        if (hasNewTraces) {
            this.$nextTick(() => {
              const el = this.$refs.traceBody
              if (el) el.scrollTop = el.scrollHeight
            })
        }
        
        this.pipelineStage = data.stage;
        this.pipelineStatus = data.status;

        this.scrollToBottom()

        if (data.status === 'completed') {
          this.forecasting = false
          clearInterval(this.pollInterval)
          
          // Instead of showing the static summary, we trigger the Supervisor to synthesize results live
          this.sendMessage('SYSTEM_TRIGGER: FORECAST_COMPLETED', true)
          
          await this.loadResultsIfMissing()
        } else if (data.status === 'failed') {
          this.forecasting = false
          clearInterval(this.pollInterval)

        }
      } catch (e) {
        console.error("Status polling error:", e)
      }
    },
    async loadResultsIfMissing() {
      if (!this.currentRunId) return
      try {
        let rows = await getResults(this.currentRunId)
        if (!rows || rows.length === 0) {
          const res = await axios.get(`/api/forecast/results/${this.currentRunId}`)
          rows = res.data.rows || []
          if (rows.length > 0) {
            await saveResults(this.currentRunId, rows)
          }
        }
      } catch (e) {
        console.error('Failed to cache results:', e)
      }
    },
    async loadTracesForRun(runId) {
      if (!runId) return
      try {
        const res = await axios.get(`/api/forecast/status/${runId}`)
        const data = res.data
        if (data.traces && data.traces.length > 0) {
          this.currentTrace = data.traces;
          this.forecastTraceCount = data.traces.length;
          console.log('Loaded', data.traces.length, 'traces for run', runId);
        }
      } catch (e) {
        console.error('Failed to load traces:', e)
      }
    },
    formatStage(stage) {
      const stageMap = {
        'starting': 'Initializing',
        'loading_data': 'Loading Data',
        'aggregating': 'Aggregating',
        'correcting': 'Correcting',
        'segmenting': 'Segmenting',
        'features': 'Features',
        'training': 'Training',
        'predicting': 'Predicting',
        'done': 'Complete'
      }
      return stageMap[stage] || stage
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.chatHistory
        if (el) {
          el.scrollTop = el.scrollHeight
        }
      })
    }
  }
}
</script>

<style scoped>
.chat-page {
  height: 100%;
  display: flex;
  width: 100%;
  flex: 1;
}

.chat-container {
  flex: 1;
  background: var(--color-bg-card);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--color-border);
}

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-card);
}

.chat-title {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 600;
  font-size: 15px;
  color: var(--color-text);
}

.chat-title svg {
  color: var(--color-primary);
}

.run-badge {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  color: var(--color-text-muted);
  background: var(--color-bg);
  padding: 5px 12px;
  border-radius: 20px;
}

.run-dot {
  width: 6px;
  height: 6px;
  background: #10B981;
  border-radius: 50%;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.clear-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 2px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: var(--transition);
}

.clear-btn:hover {
  color: var(--color-text);
  background: rgba(0, 0, 0, 0.05);
}

.chat-messages {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 20px;
  background: var(--color-bg);
}

/* Welcome State */
.welcome-state {
  display: flex;
  flex-direction: column;
  padding: 24px 4px;
}

.welcome-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 28px;
  text-align: left;
}

.welcome-header .welcome-icon {
  width: 48px;
  height: 48px;
  background: rgba(124, 58, 237, 0.1);
  color: var(--color-primary);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 0;
  flex-shrink: 0;
}

.welcome-header h2 {
  font-size: 18px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 4px 0;
}

.welcome-header p {
  font-size: 14px;
  color: var(--color-text-muted);
  margin: 0;
}

/* Suggestion Cards */
.suggestion-cards {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
}

.suggestion-cards .card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.suggestion-cards .card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
  margin-bottom: 4px;
}

.suggestion-cards .card-header svg {
  color: var(--color-primary);
}

.suggestion-cards .card-action {
  background: rgba(124, 58, 237, 0.03);
  border-color: rgba(124, 58, 237, 0.15);
}

.suggestion-cards .card-action .card-header {
  color: var(--color-primary);
}

.suggestion-cards .card-action .card-header svg {
  color: var(--color-primary);
}

.suggestion-cards button {
  background: transparent;
  border: none;
  padding: 10px 12px;
  border-radius: var(--radius-sm);
  text-align: left;
  font-size: 13px;
  color: var(--color-text);
  cursor: pointer;
  transition: var(--transition);
  line-height: 1.4;
}

.suggestion-cards button:hover {
  background: var(--color-bg);
}

.suggestion-cards button.primary {
  background: var(--color-primary);
  color: white;
  text-align: center;
  font-weight: 500;
}

.suggestion-cards button.primary:hover {
  background: #6D28D9;
}

.suggestion-cards .card-hint {
  font-size: 11px;
  color: var(--color-text-muted);
  text-align: center;
  margin: 0;
  padding-top: 4px;
}

/* Mobile: stack cards */
@media (max-width: 640px) {
  .suggestion-cards {
    grid-template-columns: 1fr;
  }
}

/* Messages */
.message {
  display: flex;
  gap: 12px;
  max-width: 90%;
}

.message.user {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message.ai, 
.message.system {
  align-self: flex-start;
}

.message .avatar {
  width: 28px;
  height: 28px;
  background: var(--color-primary);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  margin-top: 2px;
}

.message.system .avatar {
  background: #6B7280;
}

.avatar.loading {
  background: transparent;
  gap: 4px;
}

.avatar.loading span {
  width: 6px;
  height: 6px;
  background: var(--color-primary-light);
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.avatar.loading span:nth-child(1) { animation-delay: -0.32s; }
.avatar.loading span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

.message-content {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.6;
}

.user .message-content {
  background: var(--color-primary);
  color: white;
  border-bottom-right-radius: 4px;
}

.ai .message-content,
.system .message-content {
  background: var(--color-bg-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
  border-bottom-left-radius: 4px;
}

.system .message-content {
  background: var(--color-bg);
  border: 1px solid var(--color-border);
  border-left: 3px solid #6B7280;
  padding: 14px 16px;
}

.system .message-content .system-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  color: #6B7280;
  margin-bottom: 8px;
}

.system .message-content .system-badge svg {
  width: 12px;
  height: 12px;
}

.system .message-content .system-info {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.system .message-content .system-info .run-id {
  font-family: 'Fira Code', monospace;
  font-size: 12px;
  color: var(--color-primary);
  background: rgba(124, 58, 237, 0.1);
  padding: 3px 8px;
  border-radius: 4px;
}

.system .message-content .system-info .status-text {
  font-size: 12px;
  color: var(--color-text-muted);
}

.text :deep(p) {
  margin: 0 0 10px 0;
}
.text :deep(p:last-child) {
  margin: 0;
}
.text :deep(ul), .text :deep(ol) {
  margin: 10px 0;
  padding-left: 20px;
}
.text :deep(li) {
  margin: 4px 0;
}
.text :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
  font-size: 13px;
}
.text :deep(th), .text :deep(td) {
  border: 1px solid var(--color-border);
  padding: 8px 10px;
  text-align: left;
}
.text :deep(th) {
  background: var(--color-bg);
  color: var(--color-text-muted);
  font-weight: 500;
}

/* Progress */
.progress {
  min-width: 280px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.progress-stage {
  font-weight: 600;
  color: var(--color-text);
  font-size: 14px;
}

.progress-pct {
  color: var(--color-primary);
  font-weight: 700;
  font-size: 14px;
}

.progress-bar {
  height: 8px;
  background: var(--color-border);
  border-radius: 4px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: var(--color-primary);
  transition: width 0.3s ease;
}

.progress-fill.error {
  background: #EF4444;
}

.progress-msg {
  font-size: 12px;
  color: var(--color-text-muted);
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}

.progress-msg::before {
  content: '';
  width: 6px;
  height: 6px;
  background: #9CA3AF;
  border-radius: 50%;
}

.progress-done {
  margin-top: 12px;
  padding: 10px 12px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  border-radius: 8px;
  color: #059669;
  font-size: 13px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-done svg {
  flex-shrink: 0;
}

/* Input */
.input-area {
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 12px;
}

.input-area textarea {
  flex: 1;
  padding: 14px 20px;
  border: 1px solid var(--color-border);
  border-radius: 28px;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  transition: border-color 0.2s;
  background: var(--color-bg);
  resize: none;
  min-height: 24px;
  max-height: 150px;
  overflow-y: auto;
}

.input-area textarea:focus {
  border-color: var(--color-primary);
  background: var(--color-bg-card);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.08);
}

.input-area textarea::placeholder {
  color: var(--color-text-muted);
}

.send-btn {
  width: 44px;
  height: 44px;
  background: var(--color-primary);
  color: white;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: var(--transition);
  flex-shrink: 0;
}

.send-btn:hover:not(:disabled) {
  background: #6D28D9;
  transform: scale(1.05);
}

.send-btn:disabled {
  background: var(--color-border);
  cursor: not-allowed;
}

.cancel-btn {
  width: 44px;
  height: 44px;
  background: #EF4444;
  color: white;
  border: none;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: background 0.2s;
  flex-shrink: 0;
}
.cancel-btn:hover {
  background: #DC2626;
}

.workspace-wrapper {
  display: grid;
  grid-template-columns: 60% 40%;
  gap: 20px;
  height: calc(100vh - 80px);
  padding: 10px 0;
  box-sizing: border-box;
}

@media (max-width: 1024px) {
  .workspace-wrapper {
    grid-template-columns: 1fr;
    grid-template-rows: 1fr 1fr;
  }
}

.trace-panel {
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
  border-radius: 16px;
  border: 1px solid rgba(124, 58, 237, 0.2);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 4px 20px rgba(124, 58, 237, 0.1);
}

.trace-header {
  padding: 16px 20px;
  background: linear-gradient(135deg, #7C3AED 0%, #A78BFA 100%);
  border-bottom: none;
  font-weight: 700;
  color: white;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  letter-spacing: 0.3px;
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.3);
  flex-shrink: 0;
}

.trace-header svg {
  opacity: 0.9;
}

.trace-body {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
  background: rgba(255, 255, 255, 0.7);
  color: #1E293B;
  font-family: 'Fira Code', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 12px;
  line-height: 1.6;
  backdrop-filter: blur(10px);
}

.trace-empty {
  color: #64748B;
  text-align: center;
  margin-top: 40px;
  font-style: italic;
  font-size: 13px;
  padding: 20px;
  background: rgba(255, 255, 255, 0.5);
  border-radius: 12px;
  border: 1px dashed rgba(124, 58, 237, 0.3);
}

.trace-item {
  margin-bottom: 14px;
  border-radius: 10px;
  padding: 12px;
  background: white;
  border: 1px solid rgba(124, 58, 237, 0.15);
  transition: all 0.2s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
}

.trace-item:hover {
  border-color: rgba(124, 58, 237, 0.3);
  box-shadow: 0 2px 8px rgba(124, 58, 237, 0.15);
  transform: translateY(-1px);
}

.trace-item.tool_call { 
  border-left: 3px solid #7C3AED; 
  background: linear-gradient(135deg, #FAF5FF 0%, #FFFFFF 100%);
}
.trace-item.tool_result { 
  border-left: 3px solid #10B981; 
  background: linear-gradient(135deg, #ECFDF5 0%, #FFFFFF 100%);
}
.trace-item.error { 
  border-left: 3px solid #EF4444; 
  background: linear-gradient(135deg, #FEF2F2 0%, #FFFFFF 100%);
}
.trace-item.info { 
  border-left: 3px solid #6366F1; 
  background: linear-gradient(135deg, #EEF2FF 0%, #FFFFFF 100%);
}

.trace-item-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
  align-items: center;
  flex-wrap: wrap;
}

.trace-agent {
  font-size: 9px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 6px;
  letter-spacing: 0.5px;
}
.trace-agent.supervisor { 
  background: linear-gradient(135deg, #312E81 0%, #4F46E5 100%); 
  color: #C7D2FE; 
}
.trace-agent.analyst { 
  background: linear-gradient(135deg, #064E3B 0%, #059669 100%); 
  color: #A7F3D0; 
}
.trace-agent.system { 
  background: linear-gradient(135deg, #475569 0%, #64748B 100%); 
  color: #E2E8F0; 
}

.trace-name {
  color: #7C3AED;
  font-weight: 600;
  font-size: 12px;
}

.trace-content {
  background: rgba(124, 58, 237, 0.04);
  padding: 10px 14px;
  border-radius: 8px;
  white-space: pre-wrap;
  word-break: break-word;
  font-size: 11px;
  border: 1px solid rgba(124, 58, 237, 0.1);
}

.json-block pre {
  margin: 0;
  color: #7C3AED;
  font-family: 'Fira Code', ui-monospace, monospace;
}

.result-text { 
  color: #059669; 
  font-weight: 500;
}
.error-text { 
  color: #DC2626; 
  font-weight: 500;
}
.info-text { 
  color: #4F46E5; 
  font-weight: 500;
}
</style>

<style scoped>
/* New Chat Input pulsing animation */
.send-btn.pulse {
  animation: sendPulse 1.5s infinite;
  background: #A78BFA;
  cursor: wait;
}
@keyframes sendPulse {
  0% { transform: scale(1); box-shadow: 0 0 0 0 rgba(124, 58, 237, 0.4); }
  70% { transform: scale(1.05); box-shadow: 0 0 0 10px rgba(124, 58, 237, 0); }
  100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(124, 58, 237, 0); }
}

.inline-thinking {
  display: flex;
  gap: 4px;
  align-items: center;
  padding: 14px 16px !important;
}
.inline-thinking .dot {
  width: 6px;
  height: 6px;
  background: #A78BFA;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}
.inline-thinking .dot:nth-child(1) { animation-delay: -0.32s; }
.inline-thinking .dot:nth-child(2) { animation-delay: -0.16s; }

.loading-avatar {
  background: #7C3AED !important;
  color: white !important;
}

/* Base style overrides to ensure clean chat */
.message.system { display: none; }
</style>
