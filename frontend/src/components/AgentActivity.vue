<template>
  <div class="agent-activity">
    <div class="activity-header">
      <div class="header-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
        <span>Agent Activity</span>
        
        <!-- Agent Token Summary -->
        <div class="token-summary" v-if="hasAnyTokens">
          <span v-if="agentTokens.supervisor.total > 0" class="agent-token supervisor" title="Supervisor Tokens">
            👑 {{ formatNum(agentTokens.supervisor.input) }} in / {{ formatNum(agentTokens.supervisor.output) }} out
          </span>
          <span v-if="agentTokens.analyst.total > 0" class="agent-token analyst" title="Analyst Tokens">
            📊 {{ formatNum(agentTokens.analyst.input) }} in / {{ formatNum(agentTokens.analyst.output) }} out
          </span>
          <span v-if="agentTokens.system.total > 0" class="agent-token system" title="Pipeline Tokens">
            ⚙️ {{ formatNum(agentTokens.system.input) }} in / {{ formatNum(agentTokens.system.output) }} out
          </span>
        </div>
      </div>
      <div class="header-actions">
        <button @click="$emit('clear')" class="clear-btn" title="Clear Trace">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <polyline points="3 6 5 6 21 6"></polyline>
            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>
          </svg>
        </button>
      </div>
    </div>

    <div class="activity-body" ref="activityBody">
      <!-- Run ID Header -->
      <Transition name="fade-slide">
        <div v-if="currentRunId" class="run-info-card" :class="pipelineStatus">
          <div class="run-info-content">
            <div class="run-info-left">
              <div class="run-icon" :class="pipelineStatus">
                <svg v-if="pipelineStatus === 'completed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="18" height="18">
                  <polyline points="20 6 9 17 4 12"></polyline>
                </svg>
                <svg v-else-if="pipelineStatus === 'failed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
                <svg v-else-if="pipelineStatus === 'running'" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
                  <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
                  <path d="M12 2a10 10 0 0 1 10 10"></path>
                </svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
                  <circle cx="12" cy="12" r="10"></circle>
                </svg>
              </div>
              <div class="run-details">
                <div class="run-label">Run ID</div>
                <div class="run-id-value">{{ currentRunId.substring(0, 8) }}</div>
              </div>
            </div>
            <div class="run-info-right">
              <span class="status-badge" :class="pipelineStatus">
                <span v-if="pipelineStatus === 'running'" class="pulse-dot"></span>
                {{ pipelineStatus }}
              </span>
            </div>
          </div>
        </div>
      </Transition>

      <!-- Pipeline Tracker -->
      <Transition name="fade-slide">
        <PipelineStepTracker
          v-if="pipelineStatus !== 'idle' || pipelineStage !== ''"
          :currentStage="pipelineStage"
          :status="pipelineStatus"
        />
      </Transition>

      <!-- Empty State -->
      <div v-if="trace.length === 0 && pipelineStatus === 'idle'" class="empty-state">
        <div class="empty-illustration">
          <svg viewBox="0 0 120 120" fill="none" width="120" height="120">
            <!-- Background circle -->
            <circle cx="60" cy="60" r="50" fill="#F5F3FF" stroke="#DDD6FE" stroke-width="2"/>
            <!-- Clock face -->
            <circle cx="60" cy="60" r="35" fill="none" stroke="#C4B5FD" stroke-width="1.5"/>
            <!-- Hour hand -->
            <line x1="60" y1="60" x2="60" y2="40" stroke="#7C3AED" stroke-width="2.5" stroke-linecap="round"/>
            <!-- Minute hand -->
            <line x1="60" y1="60" x2="75" y2="55" stroke="#7C3AED" stroke-width="2" stroke-linecap="round"/>
            <!-- Center dot -->
            <circle cx="60" cy="60" r="4" fill="#7C3AED"/>
            <!-- Top indicator -->
            <circle cx="60" cy="22" r="3" fill="#A78BFA"/>
          </svg>
        </div>
        <h3 class="empty-title">No Activity Yet</h3>
        <p class="empty-description">
          Start a forecast or ask a question to see real-time execution logs and agent activity.
        </p>
        <div class="empty-hint">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
          Watch the pipeline progress here
        </div>
      </div>

      <!-- Activity Feed -->
      <div class="feed-container">
        <TransitionGroup name="card-list">
          <ToolCallCard
            v-for="(step, idx) in validTraces"
            :key="stepKey(step, idx)"
            :step="step"
            :isPaired="isPairedByKey(step, idx)"
          />
        </TransitionGroup>
      </div>
    </div>
  </div>
</template>

<script>
import PipelineStepTracker from './PipelineStepTracker.vue'
import ToolCallCard from './ToolCallCard.vue'

const traceKeyMap = new WeakMap();

export default {
  name: 'AgentActivity',
  components: { PipelineStepTracker, ToolCallCard },
  props: {
    currentRunId: { type: String, default: null },
    trace: { type: Array, default: () => [] },
    pipelineStage: { type: String, default: '' },
    pipelineStatus: { type: String, default: 'idle' }
  },
  computed: {
    validTraces() {
      // Filter out null/undefined/invalid trace items
      return this.trace.filter(step => step && typeof step === 'object' && step.type);
    },
    agentTokens() {
      const usage = {
        supervisor: { input: 0, output: 0, total: 0 },
        analyst: { input: 0, output: 0, total: 0 },
        system: { input: 0, output: 0, total: 0 }
      };
      
      for (const step of this.trace) {
        let inT = 0;
        let outT = 0;
        
        if (step.tokens) {
          inT = step.tokens.input || 0;
          outT = step.tokens.output || 0;
        } else if (step.usage) {
          inT = step.usage.prompt_tokens || 0;
          outT = step.usage.completion_tokens || 0;
        } else if (step.input_tokens !== undefined || step.output_tokens !== undefined) {
          inT = step.input_tokens || 0;
          outT = step.output_tokens || 0;
        }
        
        if (inT > 0 || outT > 0) {
          const agent = step.agent || 'system';
          if (!usage[agent]) {
            usage[agent] = { input: 0, output: 0, total: 0 };
          }
          usage[agent].input += inT;
          usage[agent].output += outT;
          usage[agent].total += (inT + outT);
        }
      }
      return usage;
    },
    hasAnyTokens() {
      return this.agentTokens.supervisor.total > 0 || 
             this.agentTokens.analyst.total > 0 || 
             this.agentTokens.system.total > 0;
    }
  },
  watch: {
    trace: {
      deep: true,
      handler() {
        this.scrollToBottom();
      }
    },
    pipelineStage() {
      this.scrollToBottom();
    }
  },
  methods: {
    formatNum(n) {
      if (!n) return '0';
      if (n >= 1000) {
        return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
      }
      return n.toString();
    },
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.activityBody;
        if (el) {
          const isScrolledToBottom = el.scrollHeight - el.clientHeight <= el.scrollTop + 150;
          if (isScrolledToBottom) {
            el.scrollTo({
              top: el.scrollHeight,
              behavior: 'smooth'
            });
          }
        }
      });
    },
    isPaired(idx) {
      // Check if this step is part of a call+result pair
      if (idx < this.trace.length - 1) {
        const current = this.trace[idx];
        const next = this.trace[idx + 1];
        if (current.type === 'tool_call' && next.type === 'tool_result') {
          return true;
        }
      }
      return false;
    },
    stepKey(step, idx) {
      if (step._key) return step._key;
      let key = traceKeyMap.get(step);
      if (!key) {
        key = `trace-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        traceKeyMap.set(step, key);
      }
      return key;
    },
    isPairedByKey(step, idx) {
      // Check pairing using the validTraces array
      const traces = this.validTraces;
      if (idx < traces.length - 1) {
        const current = traces[idx];
        const next = traces[idx + 1];
        if (current && next && current.type === 'tool_call' && next.type === 'tool_result') {
          return true;
        }
      }
      return false;
    }
  }
}
</script>

<style scoped>
.agent-activity {
  width: 100%;
  height: 100%;
  background: var(--color-bg);
  border-radius: var(--radius-lg);
  border: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.activity-header {
  padding: 14px 20px;
  background: var(--color-bg-card);
  border-bottom: 1px solid var(--color-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex-shrink: 0;
}

.header-title {
  font-weight: 600;
  color: var(--color-text);
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
}

.header-title svg {
  color: var(--color-primary);
}

.token-summary {
  display: flex;
  gap: 8px;
  margin-left: 16px;
  align-items: center;
}

.agent-token {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  white-space: nowrap;
  cursor: default;
}

.agent-token.supervisor {
  background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);
  color: #4338CA;
  border: 1px solid #A5B4FC;
}

.agent-token.analyst {
  background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
  color: #047857;
  border: 1px solid #6EE7B7;
}

.agent-token.system {
  background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
  color: #1D4ED8;
  border: 1px solid #93C5FD;
}

.clear-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-btn:hover {
  background: #FEE2E2;
  color: #EF4444;
}

.activity-body {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
  scroll-behavior: smooth;
}

/* Run Info Card */
.run-info-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 14px 16px;
  margin-bottom: 16px;
  transition: all 0.3s ease;
}

.run-info-card.running {
  background: linear-gradient(135deg, #FAF5FF 0%, #F3E8FF 100%);
  border-color: #DDD6FE;
}

.run-info-card.completed {
  background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
  border-color: #A7F3D0;
}

.run-info-card.failed {
  background: linear-gradient(135deg, #FEF2F2 0%, #FEE2E2 100%);
  border-color: #FECACA;
}

.run-info-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.run-info-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.run-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1F5F9;
  border-radius: 8px;
  color: #64748B;
}

.run-icon.running {
  background: #EDE9FE;
  color: #7C3AED;
}

.run-icon.completed {
  background: #D1FAE5;
  color: #059669;
}

.run-icon.failed {
  background: #FEE2E2;
  color: #DC2626;
}

.run-icon svg.spin {
  animation: spin 1s linear infinite;
}

.run-details {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.run-label {
  font-size: 10px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.run-id-value {
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-primary);
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  padding: 4px 10px;
  border-radius: 12px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.status-badge.running {
  background: #E0F2FE;
  color: #0284C7;
}

.status-badge.completed {
  background: #D1FAE5;
  color: #059669;
}

.status-badge.failed {
  background: #FEE2E2;
  color: #DC2626;
}

.status-badge.idle {
  background: #F1F5F9;
  color: #64748B;
}

.pulse-dot {
  width: 6px;
  height: 6px;
  background: currentColor;
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

/* Empty State */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 24px;
  color: var(--color-text-muted);
}

.empty-illustration {
  margin-bottom: 20px;
  opacity: 0.9;
}

.empty-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0 0 8px 0;
}

.empty-description {
  font-size: 13px;
  line-height: 1.6;
  max-width: 280px;
  margin: 0 0 16px 0;
  color: #6B7280;
}

.empty-hint {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: #9CA3AF;
  padding: 6px 12px;
  background: #F9FAFB;
  border-radius: 16px;
}

.feed-container {
  display: flex;
  flex-direction: column;
}

/* Transitions */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: all 0.3s ease;
}

.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateY(-10px);
}

.card-list-enter-active {
  transition: all 0.3s ease-out;
}

.card-list-leave-active {
  transition: all 0.2s ease-in;
}

.card-list-enter-from {
  opacity: 0;
  transform: translateY(12px);
}

.card-list-leave-to {
  opacity: 0;
  transform: translateX(-10px);
}

.card-list-move {
  transition: transform 0.3s ease;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>
