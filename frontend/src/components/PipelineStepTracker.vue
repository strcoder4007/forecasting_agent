<template>
  <div class="pipeline-tracker">
    <div class="tracker-header">
      <div class="header-left">
        <h4>Pipeline Progress</h4>
        <span class="stage-indicator">{{ currentStageName }}</span>
      </div>
      <div class="header-right">
        <span class="progress-text">{{ progressPercent }}%</span>
        <span class="status-badge" :class="status">{{ status }}</span>
      </div>
    </div>

    <div class="progress-bar-container">
      <div class="progress-bar">
        <div
          class="progress-fill"
          :class="status"
          :style="{ width: progressPercent + '%' }"
        ></div>
      </div>
      <div class="stages-row">
        <div
          v-for="(stage, index) in stages"
          :key="stage.id"
          class="stage-item"
          :class="getStageClass(stage.id, index)"
        >
          <div class="stage-icon">
            <svg v-if="isCompleted(index)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
              <polyline points="20 6 9 17 4 12"></polyline>
            </svg>
            <svg v-else-if="currentStage === stage.id && status === 'running'" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle>
              <path d="M12 2a10 10 0 0 1 10 10"></path>
            </svg>
            <svg v-else-if="currentStage === stage.id && status === 'failed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <line x1="18" y1="6" x2="6" y2="18"></line>
              <line x1="6" y1="6" x2="18" y2="18"></line>
            </svg>
            <span v-else class="dot"></span>
          </div>
          <span class="stage-label">{{ stage.shortName }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PipelineStepTracker',
  props: {
    currentStage: { type: String, default: '' },
    status: { type: String, default: 'idle' }
  },
  data() {
    return {
      stages: [
        { id: 'starting', name: 'Initializing', shortName: 'Init' },
        { id: 'exploring', name: 'Data Exploration', shortName: 'Explore' },
        { id: 'transforming', name: 'ETL & Feature Engineering', shortName: 'ETL' },
        { id: 'training', name: 'AutoML Training', shortName: 'Train' },
        { id: 'synthesizing', name: 'Result Synthesis', shortName: 'Synthesize' },
        { id: 'done', name: 'Complete', shortName: 'Done' }
      ]
    }
  },
  computed: {
    currentIndex() {
      return this.stages.findIndex(s => s.id === this.currentStage);
    },
    progressPercent() {
      if (this.status === 'completed' || this.currentStage === 'done') return 100;
      if (!this.currentStage || this.status === 'idle') return 0;
      if (this.currentIndex === -1) return 0;
      // Each stage gets equal weight, with partial for current
      return Math.round((this.currentIndex / (this.stages.length - 1)) * 100);
    },
    currentStageName() {
      const stage = this.stages.find(s => s.id === this.currentStage);
      return stage ? stage.name : 'Waiting...';
    }
  },
  methods: {
    isCompleted(index) {
      if (this.status === 'completed' || this.currentStage === 'done') return true;
      const currentIndex = this.stages.findIndex(s => s.id === this.currentStage);
      return index < currentIndex && currentIndex !== -1;
    },
    getStageClass(stageId, index) {
      if (this.status === 'completed' || this.currentStage === 'done') return 'completed';
      if (this.currentStage === stageId && this.status === 'running') return 'active';
      if (this.currentStage === stageId && this.status === 'failed') return 'error';
      if (this.isCompleted(index)) return 'completed';
      return 'pending';
    }
  }
}
</script>

<style scoped>
.pipeline-tracker {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px 20px;
  margin-bottom: 20px;
}

.tracker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--color-text);
}

.stage-indicator {
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  padding: 2px 8px;
  background: rgba(124, 58, 237, 0.1);
  border-radius: 4px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.progress-text {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text-muted);
}

.status-badge {
  font-size: 10px;
  padding: 3px 8px;
  border-radius: 12px;
  text-transform: uppercase;
  font-weight: 700;
  letter-spacing: 0.5px;
}

.status-badge.running { background: #E0F2FE; color: #0284C7; }
.status-badge.completed { background: #D1FAE5; color: #059669; }
.status-badge.failed { background: #FEE2E2; color: #DC2626; }
.status-badge.idle { background: #F1F5F9; color: #64748B; }

.progress-bar-container {
  position: relative;
}

.progress-bar {
  height: 6px;
  background: #E5E7EB;
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 16px;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.5s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-fill.running {
  background: linear-gradient(90deg, #7C3AED 0%, #A78BFA 100%);
}

.progress-fill.completed {
  background: linear-gradient(90deg, #059669 0%, #10B981 100%);
}

.progress-fill.failed {
  background: linear-gradient(90deg, #DC2626 0%, #EF4444 100%);
}

.progress-fill.idle {
  background: #E5E7EB;
}

.stages-row {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.stage-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  flex: 1;
  opacity: 0.4;
  transition: opacity 0.3s ease;
}

.stage-item.active,
.stage-item.completed {
  opacity: 1;
}

.stage-item.error {
  opacity: 1;
}

.stage-icon {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #F1F5F9;
  border-radius: 50%;
  color: #94A3B8;
  transition: all 0.3s ease;
  flex-shrink: 0;
}

.stage-item.completed .stage-icon {
  background: #D1FAE5;
  color: #059669;
}

.stage-item.active .stage-icon {
  background: #EDE9FE;
  color: #7C3AED;
  box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.2);
}

.stage-item.error .stage-icon {
  background: #FEE2E2;
  color: #DC2626;
}

.stage-icon svg {
  width: 14px;
  height: 14px;
}

.stage-icon .dot {
  width: 8px;
  height: 8px;
  background: currentColor;
  border-radius: 50%;
}

.stage-icon svg.spin {
  animation: spin 1s linear infinite;
}

.stage-label {
  font-size: 11px;
  font-weight: 500;
  color: var(--color-text-muted);
  text-align: center;
  white-space: nowrap;
}

.stage-item.active .stage-label {
  color: #7C3AED;
  font-weight: 600;
}

.stage-item.completed .stage-label {
  color: #059669;
}

.stage-item.error .stage-label {
  color: #DC2626;
}

@keyframes spin {
  100% { transform: rotate(360deg); }
}
</style>
