<template>
  <div class="tool-card" :class="[borderColorClass]">
    <div class="tool-header">
      <span class="agent-badge" :class="agentClass">{{ agentName }}</span>
      <span class="tool-name">{{ step.name || 'Log' }}</span>
      <span class="time">{{ timeFormatted }}</span>
    </div>
    
    <div class="tool-body">
      <!-- Info / Error messages -->
      <div v-if="step.type === 'info'" class="info-text">{{ step.message }}</div>
      <div v-if="step.type === 'error'" class="error-text">{{ step.message }}</div>
      
      <!-- Tool Calls (Inputs) -->
      <div v-if="step.type === 'tool_call'">
        <div v-if="isSqlCall" class="summary">Executing Query...</div>
        <SqlViewer v-if="isSqlCall" :sql="sqlQuery" />
        
        <div v-else-if="isPythonCall" class="summary">Executing Python Code...</div>
        <SqlViewer v-else-if="isPythonCall" :sql="pythonCode" />
        
        <div v-else-if="isSimulateCall" class="summary">
          Simulating Promotion: SKU {{ step.args.sku_id }}, Store {{ step.args.store_id }} @ {{ (step.args.discount_pct * 100).toFixed(0) }}% off
        </div>
        
        <div v-else class="summary">
          <div class="expandable" @click="expanded = !expanded">
            <span class="toggle-icon">{{ expanded ? '▼' : '▶' }}</span> View Payload
          </div>
          <pre v-if="expanded" class="raw-json">{{ formatArgs(step.args) }}</pre>
        </div>
      </div>
      
      <!-- Tool Results (Outputs) -->
      <div v-if="step.type === 'tool_result'">
        <div v-if="isPythonResult" class="result-text python-result">
          <pre>{{ step.result }}</pre>
        </div>
        <div v-else class="result-text">{{ step.result }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import SqlViewer from './SqlViewer.vue'

export default {
  name: 'ToolCallCard',
  components: { SqlViewer },
  props: {
    step: { type: Object, required: true }
  },
  data() {
    return {
      expanded: false,
      timestamp: new Date()
    }
  },
  computed: {
    borderColorClass() {
      if (this.step.type === 'tool_call') return 'border-purple';
      if (this.step.type === 'tool_result') return 'border-green';
      if (this.step.type === 'error') return 'border-red';
      if (this.step.agent === 'system') return 'border-blue';
      if (this.step.type === 'info' && this.step.message?.includes('WMAPE')) return 'border-teal'; // Custom for routing logs
      return 'border-gray';
    },
    agentClass() {
      return this.step.agent || 'system';
    },
    agentName() {
      if (this.step.agent === 'supervisor') return 'TIER 1 (SUPERVISOR)';
      if (this.step.agent === 'analyst') return 'TIER 2 (ANALYST)';
      if (this.step.agent === 'system') return 'PIPELINE';
      return (this.step.agent || 'system').toUpperCase();
    },
    timeFormatted() {
      return this.timestamp.toLocaleTimeString([], { hour12: false });
    },
    isSqlCall() {
      return this.step.name === 'execute_sql' && this.step.args && this.step.args.query;
    },
    sqlQuery() {
      return this.step.args?.query || '';
    },
    isPythonCall() {
      return this.step.name === 'execute_python' && this.step.args && this.step.args.code;
    },
    pythonCode() {
      return this.step.args?.code || '';
    },
    isSimulateCall() {
      return this.step.name === 'simulate_promotion' && this.step.args;
    },
    isPythonResult() {
      return this.step.name === 'execute_python';
    }
  },
  methods: {
    formatArgs(args) {
      if (!args || Object.keys(args).length === 0) return '{}';
      return JSON.stringify(args, null, 2);
    }
  }
}
</script>

<style scoped>
.tool-card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  margin-bottom: 12px;
  border-left-width: 4px;
  box-shadow: var(--shadow-sm);
  overflow: hidden;
  animation: slideIn 0.3s ease-out forwards;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateX(10px); }
  to { opacity: 1; transform: translateX(0); }
}

.border-purple { border-left-color: #8B5CF6; }
.border-green { border-left-color: #10B981; }
.border-red { border-left-color: #EF4444; }
.border-blue { border-left-color: #3B82F6; }
.border-gray { border-left-color: #9CA3AF; }
.border-teal { border-left-color: #14B8A6; }

.tool-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--color-bg);
  border-bottom: 1px solid var(--color-border);
}

.agent-badge {
  font-size: 10px;
  font-weight: 700;
  padding: 2px 6px;
  border-radius: 4px;
  letter-spacing: 0.5px;
}
.agent-badge.supervisor { background: #E0E7FF; color: #4338CA; }
.agent-badge.analyst { background: #D1FAE5; color: #047857; }
.agent-badge.system { background: #DBEAFE; color: #1D4ED8; }

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
  flex: 1;
}

.time {
  font-size: 11px;
  color: var(--color-text-muted);
}

.tool-body {
  padding: 12px;
  font-size: 13px;
}

.info-text { color: var(--color-text); }
.error-text { color: #EF4444; font-weight: 500; }
.result-text { color: #059669; font-weight: 500; }
.summary { color: var(--color-text-muted); }

.expandable {
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  user-select: none;
  font-size: 12px;
  color: var(--color-primary);
  font-weight: 500;
  margin-top: 4px;
}
.toggle-icon { font-size: 10px; }

.raw-json {
  margin-top: 8px;
  background: #1E1E1E;
  color: #D4D4D4;
  padding: 10px;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  overflow-x: auto;
}

.python-result pre {
  margin: 0;
  padding: 10px;
  background: #1e1e1e;
  color: #D4D4D4;
  border-radius: 4px;
  font-family: ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
  font-size: 11px;
  overflow-x: auto;
  border-left: 3px solid #10B981;
}
</style>