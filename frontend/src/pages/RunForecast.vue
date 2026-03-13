<template>
  <div class="chat-page">
    <div class="chat-container">
      <div class="chat-header">
        <div v-if="currentRunId" class="run-badge">
          <span class="run-dot"></span>
          Run {{ currentRunId.substring(0, 6) }}
          <button @click="clearRunContext" class="clear-btn" title="Clear context">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
          </button>
        </div>
      </div>

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

        <div 
          v-for="(msg, idx) in messages" 
          :key="idx"
          class="message"
          :class="msg.role"
        >
          <div v-if="msg.role === 'ai' || msg.role === 'system'" class="avatar">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
              <circle cx="12" cy="12" r="10"></circle>
              <path d="M12 16v-4"></path>
              <path d="M12 8h.01"></path>
            </svg>
          </div>
          
          <div class="message-content">
            <div v-if="msg.type === 'text'" class="text" v-html="formatMessage(msg.content)"></div>
            
            <div v-if="msg.type === 'progress'" class="progress">
              <div class="progress-header">
                <span class="progress-stage">{{ msg.content.stageTitle }}</span>
                <span class="progress-pct">{{ Math.round(msg.content.progress) }}%</span>
              </div>
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: msg.content.progress + '%' }" :class="{ error: msg.content.error }"></div>
              </div>
              <div class="progress-msg">{{ msg.content.message }}</div>
              
              <div v-if="msg.content.status === 'completed'" class="progress-done">
                Forecast complete. Ask me anything about the results.
              </div>
            </div>
          </div>
        </div>

        <div v-if="loading" class="message ai">
          <div class="avatar loading">
            <span></span><span></span><span></span>
          </div>
        </div>
      </div>

      <div class="input-area">
        <input 
          v-model="query" 
          @keyup.enter="sendMessage"
          type="text" 
          placeholder="Ask something or run a forecast..." 
          :disabled="loading || forecasting"
        />
        <button @click="sendMessage" :disabled="!query.trim() || loading || forecasting" class="send-btn">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
            <line x1="22" y1="2" x2="11" y2="13"></line>
            <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'
import { marked } from 'marked'
import { saveResults, getResults } from '../utils/db'

export default {
  name: 'RunForecast',
  data() {
    return {
      query: '',
      messages: [],
      loading: false,
      forecasting: false,
      currentRunId: null,
      pollInterval: null
    }
  },
  async mounted() {
    if (this.$route.query.id) {
      this.currentRunId = this.$route.query.id;
      this.messages.push({
        role: 'system',
        type: 'text',
        content: `**Context Loaded:** Loaded run \`${this.currentRunId.substring(0, 6)}\`. Ask me about this forecast.`
      })
      await this.loadResultsIfMissing()
    }
  },
  beforeUnmount() {
    if (this.pollInterval) clearInterval(this.pollInterval)
  },
  methods: {
    formatMessage(text) {
      return marked(text)
    },
    sendQuick(text) {
      this.query = text
      this.sendMessage()
    },
    clearRunContext() {
      this.currentRunId = null;
      this.messages.push({
        role: 'system',
        type: 'text',
        content: `*Context cleared.*`
      })
      if (this.$route.query.id) {
        this.$router.replace({ query: {} })
      }
    },
    async sendMessage() {
      if (!this.query.trim() || this.loading || this.forecasting) return

      const userText = this.query.trim()
      this.query = ''
      
      this.messages.push({ role: 'user', type: 'text', content: userText })
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
        this.scrollToBottom()
      }
    },
    async startForecast() {
      this.forecasting = true
      try {
        const res = await axios.post('/api/forecast/run')
        this.currentRunId = res.data.run_id
        
        const progMsgIndex = this.messages.length
        this.messages.push({
          role: 'system',
          type: 'progress',
          content: {
            progress: 0,
            stageTitle: 'Starting',
            message: 'Initializing forecast...',
            status: 'running',
            error: null
          }
        })
        
        this.pollInterval = setInterval(() => this.checkForecastStatus(progMsgIndex), 1500)
        this.$router.replace({ query: { id: this.currentRunId } })

      } catch (e) {
        this.messages.push({ role: 'system', type: 'text', content: `**Failed to start forecast:** ${e.response?.data?.detail || e.message}` })
        this.forecasting = false
      }
    },
    async checkForecastStatus(msgIndex) {
      if (!this.currentRunId) return
      try {
        const res = await axios.get(`/api/forecast/status/${this.currentRunId}`)
        const data = res.data
        
        const msg = this.messages[msgIndex]
        msg.content.progress = data.progress
        msg.content.stageTitle = this.formatStage(data.stage)
        msg.content.message = data.message
        msg.content.status = data.status

        this.scrollToBottom()

        if (data.status === 'completed') {
          this.forecasting = false
          clearInterval(this.pollInterval)
          await this.loadResultsIfMissing()
        } else if (data.status === 'failed') {
          this.forecasting = false
          clearInterval(this.pollInterval)
          msg.content.error = data.message
          this.messages.push({ role: 'system', type: 'text', content: `**Forecast Failed:** ${data.message}` })
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
  height: calc(100vh - 120px);
  display: flex;
  justify-content: center;
}

.chat-container {
  width: 100%;
  max-width: 960px;
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

.avatar {
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
  font-size: 13px;
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
  min-width: 240px;
}

.progress-header {
  display: flex;
  justify-content: space-between;
  font-size: 13px;
  margin-bottom: 8px;
}

.progress-stage {
  font-weight: 500;
  color: var(--color-text);
}

.progress-pct {
  color: var(--color-primary);
  font-weight: 600;
}

.progress-bar {
  height: 6px;
  background: var(--color-border);
  border-radius: 3px;
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
  margin-top: 6px;
}

.progress-done {
  margin-top: 10px;
  color: #10B981;
  font-size: 13px;
  font-weight: 500;
}

/* Input */
.input-area {
  padding: 16px 20px;
  background: var(--color-bg-card);
  border-top: 1px solid var(--color-border);
  display: flex;
  gap: 12px;
}

.input-area input {
  flex: 1;
  padding: 14px 20px;
  border: 1px solid var(--color-border);
  border-radius: 28px;
  outline: none;
  font-size: 14px;
  font-family: inherit;
  transition: var(--transition);
  background: var(--color-bg);
}

.input-area input:focus {
  border-color: var(--color-primary);
  background: var(--color-bg-card);
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.08);
}

.input-area input::placeholder {
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
</style>
