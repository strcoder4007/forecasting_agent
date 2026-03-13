<template>
  <div class="agent-activity">
    <div class="activity-header">
      <div class="header-title">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
          <polyline points="4 17 10 11 4 5"></polyline>
          <line x1="12" y1="19" x2="20" y2="19"></line>
        </svg>
        Run Details
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
      <div v-if="currentRunId" class="run-info-card">
        <div class="run-info-row">
          <span class="label">Run ID:</span>
          <span class="value run-id">{{ currentRunId.substring(0, 8) }}</span>
          <span class="status-badge" :class="pipelineStatus">{{ pipelineStatus }}</span>
        </div>
      </div>

      <!-- Pipeline Tracker -->
      <PipelineStepTracker 
        v-if="pipelineStatus !== 'idle' || pipelineStage !== ''" 
        :currentStage="pipelineStage" 
        :status="pipelineStatus" 
      />

      <!-- Activity Feed -->
      <div v-if="trace.length === 0 && pipelineStatus === 'idle'" class="empty-state">
        <div class="empty-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" width="32" height="32">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
        </div>
        <p>No agent activity yet.<br>Start a forecast or ask a question to see real-time execution logs.</p>
      </div>

      <div class="feed-container">
        <ToolCallCard 
          v-for="(step, idx) in trace" 
          :key="idx" 
          :step="step" 
        />
      </div>
    </div>
  </div>
</template>

<script>
import PipelineStepTracker from './PipelineStepTracker.vue'
import ToolCallCard from './ToolCallCard.vue'

export default {
  name: 'AgentActivity',
  components: { PipelineStepTracker, ToolCallCard },
  props: {
    currentRunId: { type: String, default: null },
    trace: { type: Array, default: () => [] },
    pipelineStage: { type: String, default: '' },
    pipelineStatus: { type: String, default: 'idle' }
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
    scrollToBottom() {
      this.$nextTick(() => {
        const el = this.$refs.activityBody;
        if (el) {
          // Only auto scroll if we are already near the bottom to avoid yanking the user
          const isScrolledToBottom = el.scrollHeight - el.clientHeight <= el.scrollTop + 150;
          if (isScrolledToBottom) {
            el.scrollTop = el.scrollHeight;
          }
        }
      });
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
  padding: 16px 20px;
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

.clear-btn {
  background: transparent;
  border: none;
  color: var(--color-text-muted);
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
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

.run-info-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  margin-bottom: 20px;
}
.run-info-row {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
}
.run-info-row .label {
  color: var(--color-text-muted);
  font-weight: 500;
}
.run-info-row .run-id {
  font-family: monospace;
  font-weight: 600;
  color: var(--color-primary);
  background: rgba(124, 58, 237, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
}
.status-badge {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 12px;
  text-transform: uppercase;
  font-weight: 700;
  margin-left: auto;
}
.status-badge.running { background: #E0F2FE; color: #0284C7; }
.status-badge.completed { background: #D1FAE5; color: #059669; }
.status-badge.failed { background: #FEE2E2; color: #DC2626; }
.status-badge.idle { background: #F1F5F9; color: #64748B; }

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px 20px;
  color: var(--color-text-muted);
  font-size: 14px;
}
.empty-icon {
  margin-bottom: 12px;
  opacity: 0.5;
}

.feed-container {
  display: flex;
  flex-direction: column;
}
</style>