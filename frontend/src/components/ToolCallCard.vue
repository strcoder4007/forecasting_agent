<template>
  <div class="tool-card" :class="cardTypeClass">
    <div class="tool-header">
      <div class="header-left">
        <span class="type-badge" :class="typeBadgeClass">
          <span class="type-icon" v-html="typeIcon"></span>
          {{ typeLabel }}
        </span>
        <span class="agent-badge" :class="agentClass">
          <span class="badge-icon">{{ agentIcon }}</span>
          {{ agentName }}
        </span>
      </div>
      <div class="header-right">
        <span class="tool-name">{{ step.name || 'Log' }}</span>
        <span class="time" :class="{ 'has-error': step.type === 'error' }">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12">
            <circle cx="12" cy="12" r="10"></circle>
            <polyline points="12 6 12 12 16 14"></polyline>
          </svg>
          {{ timeFormatted }}
        </span>
        <span v-if="hasTokens" class="token-badge" :title="`Total: ${totalTokens} tokens`">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="10" height="10">
            <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
            <path d="M2 17l10 5 10-5"></path>
            <path d="M2 12l10 5 10-5"></path>
          </svg>
          {{ tokenDisplay }}
        </span>
      </div>
    </div>

    <div class="tool-body">
      <!-- Info messages -->
      <div v-if="step.type === 'info'" class="message-box info">
        <div class="message-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        </div>
        <div class="message-content">{{ step.message }}</div>
      </div>

      <!-- Error messages -->
      <div v-if="step.type === 'error'" class="message-box error">
        <div class="message-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="16" height="16">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="15" y1="9" x2="9" y2="15"></line>
            <line x1="9" y1="9" x2="15" y2="15"></line>
          </svg>
        </div>
        <div class="message-content">{{ step.message }}</div>
      </div>

      <!-- Tool Calls (Inputs) -->
      <div v-if="step.type === 'tool_call'" class="tool-call-section">
        <div v-if="isSqlCall" class="code-block sql">
          <div class="code-header">
            <span class="code-lang">SQL</span>
          </div>
          <SqlViewer :sql="sqlQuery" />
        </div>

        <div v-else-if="isPythonCall" class="code-block python">
          <div class="code-header">
            <span class="code-lang">Python</span>
          </div>
          <SqlViewer :sql="pythonCode" />
        </div>

        <div v-else-if="isSimulateCall" class="simulation-block">
          <div class="sim-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="18" height="18">
              <path d="M12 2L2 7l10 5 10-5-10-5z"></path>
              <path d="M2 17l10 5 10-5"></path>
              <path d="M2 12l10 5 10-5"></path>
            </svg>
          </div>
          <div class="sim-details">
            <div class="sim-title">Simulating Promotion</div>
            <div class="sim-params">
              <span class="param"><strong>SKU:</strong> {{ step.args.sku_id }}</span>
              <span class="param"><strong>Store:</strong> {{ step.args.store_id }}</span>
              <span class="param"><strong>Discount:</strong> {{ (step.args.discount_pct * 100).toFixed(0) }}%</span>
            </div>
          </div>
        </div>

        <div v-else class="payload-section">
          <button class="expand-toggle" @click="expanded = !expanded">
            <span class="toggle-icon" :class="{ rotated: expanded }">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="14" height="14">
                <polyline points="9 18 15 12 9 6"></polyline>
              </svg>
            </span>
            {{ expanded ? 'Hide' : 'View' }} Payload
          </button>
          <Transition name="expand">
            <pre v-if="expanded" class="raw-json">{{ formatArgs(step.args) }}</pre>
          </Transition>
        </div>
      </div>

      <!-- Tool Results (Outputs) -->
      <div v-if="step.type === 'tool_result'" class="tool-result-section">
        <div v-if="isPythonResult" class="result-output python">
          <pre>{{ step.result }}</pre>
        </div>
        <div v-else class="result-output">{{ step.result }}</div>
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
    step: { type: Object, required: true },
    isPaired: { type: Boolean, default: false }
  },
  data() {
    return {
      expanded: false,
      timestamp: new Date()
    }
  },
  computed: {
    cardTypeClass() {
      if (this.step.type === 'tool_call') return 'type-tool-call';
      if (this.step.type === 'tool_result') return 'type-tool-result';
      if (this.step.type === 'error') return 'type-error';
      if (this.step.type === 'info') return 'type-info';
      return 'type-default';
    },
    typeBadgeClass() {
      if (this.step.type === 'tool_call') return 'badge-call';
      if (this.step.type === 'tool_result') return 'badge-result';
      if (this.step.type === 'error') return 'badge-error';
      if (this.step.type === 'info') return 'badge-info';
      return 'badge-default';
    },
    typeLabel() {
      if (this.step.type === 'tool_call') return 'Input';
      if (this.step.type === 'tool_result') return 'Output';
      if (this.step.type === 'error') return 'Error';
      if (this.step.type === 'info') return 'Info';
      return 'Log';
    },
    typeIcon() {
      if (this.step.type === 'tool_call') return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>';
      if (this.step.type === 'tool_result') return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><polyline points="20 6 9 17 4 12"></polyline></svg>';
      if (this.step.type === 'error') return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="12" cy="12" r="10"></circle><line x1="15" y1="9" x2="9" y2="15"></line><line x1="9" y1="9" x2="15" y2="15"></line></svg>';
      if (this.step.type === 'info') return '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="12" height="12"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>';
      return '';
    },
    agentClass() {
      return this.step.agent || 'system';
    },
    agentIcon() {
      if (this.step.agent === 'supervisor') return '👑';
      if (this.step.agent === 'analyst') return '📊';
      if (this.step.agent === 'system') return '⚙️';
      return '🔧';
    },
    agentName() {
      if (this.step.agent === 'supervisor') return 'Supervisor';
      if (this.step.agent === 'analyst') return 'Analyst';
      if (this.step.agent === 'system') return 'Pipeline';
      return (this.step.agent || 'system');
    },
    timeFormatted() {
      return this.timestamp.toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
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
    },
    hasTokens() {
      const step = this.step;
      // Check various token data formats
      if (step.tokens && (step.tokens.input !== undefined || step.tokens.output !== undefined)) return true;
      if (step.usage && (step.usage.prompt_tokens !== undefined || step.usage.completion_tokens !== undefined)) return true;
      if (step.input_tokens !== undefined || step.output_tokens !== undefined) return true;
      return false;
    },
    inputTokens() {
      const step = this.step;
      if (step.tokens?.input !== undefined) return step.tokens.input;
      if (step.usage?.prompt_tokens !== undefined) return step.usage.prompt_tokens;
      if (step.input_tokens !== undefined) return step.input_tokens;
      return 0;
    },
    outputTokens() {
      const step = this.step;
      if (step.tokens?.output !== undefined) return step.tokens.output;
      if (step.usage?.completion_tokens !== undefined) return step.usage.completion_tokens;
      if (step.output_tokens !== undefined) return step.output_tokens;
      return 0;
    },
    totalTokens() {
      return this.inputTokens + this.outputTokens;
    },
    tokenDisplay() {
      const formatNum = (n) => {
        if (n >= 1000) {
          return (n / 1000).toFixed(1).replace(/\.0$/, '') + 'K';
        }
        return n.toString();
      };
      return `${formatNum(this.inputTokens)} in / ${formatNum(this.outputTokens)} out`;
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
/* Base card with subtle depth */
.tool-card {
  background: #ffffff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04), 0 1px 2px rgba(0, 0, 0, 0.06);
  overflow: hidden;
  animation: slideIn 0.25s cubic-bezier(0.16, 1, 0.3, 1) forwards;
  transition: box-shadow 0.2s ease, transform 0.2s ease, border-color 0.2s ease;
}

/* Hover state with lift effect */
.tool-card:hover {
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.08), 0 4px 10px rgba(0, 0, 0, 0.04);
  transform: translateY(-2px);
  border-color: #cbd5e1;
}

/* Type-specific background hues */
.tool-card.type-tool-call {
  background: linear-gradient(135deg, #eef2ff 0%, #ffffff 60%);
}

.tool-card.type-tool-result {
  background: linear-gradient(135deg, #ecfdf5 0%, #ffffff 60%);
}

.tool-card.type-error {
  background: linear-gradient(135deg, #fef2f2 0%, #ffffff 60%);
}

.tool-card.type-info {
  background: linear-gradient(135deg, #f0f9ff 0%, #ffffff 60%);
}

/* Animation - smooth entrance */
@keyframes slideIn {
  from { 
    opacity: 0; 
    transform: translateY(12px) scale(0.98); 
  }
  to { 
    opacity: 1; 
    transform: translateY(0) scale(1); 
  }
}

/* Header - cleaner layout */
.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: linear-gradient(180deg, #fafbfc 0%, #f8fafc 100%);
  border-bottom: 1px solid #f1f5f9;
  gap: 12px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* Type badge - refined pill style */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  font-weight: 700;
  padding: 5px 12px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.type-icon {
  display: flex;
  align-items: center;
}

.type-badge.badge-call {
  background: #e0e7ff;
  color: #4338ca;
  border: 1px solid #c7d2fe;
}

.type-badge.badge-result {
  background: #d1fae5;
  color: #047857;
  border: 1px solid #a7f3d0;
}

.type-badge.badge-error {
  background: #fee2e2;
  color: #b91c1c;
  border: 1px solid #fecaca;
}

.type-badge.badge-info {
  background: #e0f2fe;
  color: #0369a1;
  border: 1px solid #bae6fd;
}

.type-badge.badge-default {
  background: #f1f5f9;
  color: #475569;
  border: 1px solid #e2e8f0;
}

/* Agent badge - more distinct */
.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 600;
  padding: 5px 12px;
  border-radius: 6px;
  letter-spacing: 0.2px;
  border: 1px solid transparent;
}

.agent-badge.supervisor {
  background: linear-gradient(135deg, #eef2ff 0%, #e0e7ff 100%);
  color: #4338ca;
  border-color: #c7d2fe;
}

.agent-badge.analyst {
  background: linear-gradient(135deg, #ecfdf5 0%, #d1fae5 100%);
  color: #047857;
  border-color: #a7f3d0;
}

.agent-badge.system {
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  color: #1d4ed8;
  border-color: #bfdbfe;
}

/* Header right section */
.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: #1e293b;
}

.time {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  color: #94a3b8;
  font-family: 'SF Mono', 'Monaco', 'Consolas', monospace;
  white-space: nowrap;
}

.token-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 600;
  color: #6366f1;
  background: #e0e7ff;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid #c7d2fe;
  white-space: nowrap;
}

.token-badge svg {
  flex-shrink: 0;
}

/* Body - improved spacing */
.tool-body {
  padding: 14px 16px;
  font-size: 13px;
  line-height: 1.6;
}

/* Message boxes - cleaner look */
.message-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid;
}

.message-box.info {
  background: #f0f9ff;
  border-color: #bae6fd;
}

.message-box.info .message-icon {
  color: #0284c7;
}

.message-box.error {
  background: #fef2f2;
  border-color: #fecaca;
}

.message-box.error .message-icon {
  color: #dc2626;
}

.message-icon {
  flex-shrink: 0;
  margin-top: 2px;
}

.message-content {
  color: #334155;
  line-height: 1.6;
}

/* Tool sections */
.tool-call-section,
.tool-result-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Code blocks - refined dark theme */
.code-block {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #334155;
}

.code-header {
  padding: 8px 14px;
  background: #0f172a;
  border-bottom: 1px solid #1e293b;
}

.code-lang {
  font-size: 10px;
  font-weight: 700;
  color: #94a3b8;
  text-transform: uppercase;
  letter-spacing: 0.8px;
}

/* Simulation block - polished */
.simulation-block {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px;
  background: linear-gradient(135deg, #f5f3ff 0%, #ede9fe 100%);
  border: 1px solid #c4b5fd;
  border-radius: 8px;
}

.sim-icon {
  width: 40px;
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #6366f1;
  color: white;
  border-radius: 10px;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(99, 102, 241, 0.3);
}

.sim-details {
  flex: 1;
}

.sim-title {
  font-weight: 600;
  color: #5b21b6;
  font-size: 13px;
  margin-bottom: 4px;
}

.sim-params {
  display: flex;
  flex-wrap: wrap;
  gap: 14px;
  font-size: 12px;
  color: #64748b;
}

.sim-params strong {
  color: #334155;
}

/* Payload section */
.payload-section {
  display: flex;
  flex-direction: column;
}

.expand-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background: transparent;
  border: none;
  cursor: pointer;
  font-size: 12px;
  color: #6366f1;
  font-weight: 600;
  padding: 6px 0;
  transition: color 0.15s ease;
}

.expand-toggle:hover {
  color: #4338ca;
}

.toggle-icon {
  display: flex;
  align-items: center;
  transition: transform 0.2s ease;
}

.toggle-icon.rotated {
  transform: rotate(90deg);
}

.raw-json {
  margin-top: 10px;
  background: #0f172a;
  color: #e2e8f0;
  padding: 14px;
  border-radius: 8px;
  font-family: 'SF Mono', 'ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', monospace;
  font-size: 11px;
  line-height: 1.6;
  overflow-x: auto;
  border: 1px solid #334155;
}

/* Expand transition - smooth */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}

/* Result output - refined */
.result-output {
  padding: 12px 14px;
  background: #ecfdf5;
  border: 1px solid #a7f3d0;
  border-radius: 8px;
  color: #047857;
  font-weight: 500;
  font-size: 12px;
}

.result-output.python {
  background: #0c1222;
  color: #38bdf8;
  font-family: 'SF Mono', 'ui-monospace', 'SFMono-Regular', 'Monaco', monospace;
  font-size: 11px;
  line-height: 1.6;
  padding: 14px;
  border-radius: 8px;
  border-left: 3px solid #10b981;
}

.result-output.python pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}

/* Responsive adjustments */
@media (max-width: 640px) {
  .tool-header {
    padding: 10px 12px;
  }
  
  .tool-body {
    padding: 12px;
  }
  
  .header-right {
    gap: 8px;
  }
  
  .type-badge,
  .agent-badge {
    padding: 4px 8px;
    font-size: 10px;
  }
}
</style>
