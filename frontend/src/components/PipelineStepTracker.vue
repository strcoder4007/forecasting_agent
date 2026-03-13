<template>
  <div class="pipeline-tracker">
    <div class="tracker-header">
      <h4>Pipeline Progress</h4>
      <span class="status-badge" :class="status">{{ status }}</span>
    </div>
    
    <div class="steps-container">
      <div 
        v-for="(stage, index) in stages" 
        :key="stage.id"
        class="step"
        :class="{
          'active': currentStage === stage.id && status === 'running',
          'completed': isCompleted(index),
          'error': currentStage === stage.id && status === 'failed',
          'pending': !isCompleted(index) && currentStage !== stage.id
        }"
      >
        <div class="step-indicator">
          <div class="icon">
            <svg v-if="isCompleted(index)" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"></polyline></svg>
            <svg v-else-if="currentStage === stage.id && status === 'running'" class="spin" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10" stroke-opacity="0.25"></circle><path d="M12 2a10 10 0 0 1 10 10"></path></svg>
            <svg v-else-if="currentStage === stage.id && status === 'failed'" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>
            <span v-else class="dot"></span>
          </div>
          <div v-if="index < stages.length - 1" class="line"></div>
        </div>
        <div class="step-content">
          <div class="step-name">{{ stage.name }}</div>
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
        { id: 'starting', name: 'Initializing' },
        { id: 'loading_data', name: 'Loading Data' },
        { id: 'aggregating', name: 'Aggregating' },
        { id: 'correcting', name: 'False-Zero Correction' },
        { id: 'segmenting', name: 'Segmentation' },
        { id: 'features', name: 'Feature Engineering' },
        { id: 'training', name: 'Model Training' },
        { id: 'predicting', name: 'Forecasting' },
        { id: 'done', name: 'Complete' }
      ]
    }
  },
  methods: {
    isCompleted(index) {
      if (this.status === 'completed' || this.currentStage === 'done') return true;
      const currentIndex = this.stages.findIndex(s => s.id === this.currentStage);
      return index < currentIndex && currentIndex !== -1;
    }
  }
}
</script>

<style scoped>
.pipeline-tracker {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 16px;
  margin-bottom: 20px;
}
.tracker-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.tracker-header h4 {
  margin: 0;
  font-size: 14px;
  color: var(--color-text);
}
.status-badge {
  font-size: 11px;
  padding: 2px 8px;
  border-radius: 12px;
  text-transform: uppercase;
  font-weight: 600;
}
.status-badge.running { background: #E0F2FE; color: #0284C7; }
.status-badge.completed { background: #D1FAE5; color: #059669; }
.status-badge.failed { background: #FEE2E2; color: #DC2626; }
.status-badge.idle { background: #F1F5F9; color: #64748B; }

.steps-container {
  display: flex;
  flex-direction: column;
  gap: 0;
}

.step {
  display: flex;
  gap: 12px;
  opacity: 0.5;
}
.step.active { opacity: 1; }
.step.completed { opacity: 0.8; }
.step.error { opacity: 1; }

.step-indicator {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 20px;
}

.icon {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--color-bg);
  border-radius: 50%;
  color: var(--color-text-muted);
}
.step.completed .icon { color: #10B981; }
.step.active .icon { color: #2563EB; }
.step.error .icon { color: #EF4444; }

.icon svg { width: 14px; height: 14px; }
.icon .dot { width: 6px; height: 6px; background: currentColor; border-radius: 50%; }
.icon svg.spin { animation: spin 1s linear infinite; }

.line {
  width: 2px;
  height: 16px;
  background: var(--color-border);
  margin: 2px 0;
}
.step.completed .line { background: #10B981; }

.step-content {
  padding-bottom: 12px;
  display: flex;
  align-items: center;
}
.step:last-child .step-content { padding-bottom: 0; }

.step-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
}

@keyframes spin { 100% { transform: rotate(360deg); } }
</style>