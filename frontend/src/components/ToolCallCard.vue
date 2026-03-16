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
.tool-card {
  background: var(--color-bg-card, #fff);
  border: 1px solid var(--color-border, #e5e7eb);
  border-radius: 12px;
  margin-bottom: 10px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  animation: slideIn 0.2s ease-out forwards;
  transition: all 0.15s ease;
}

.tool-card:hover {
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-1px);
}

/* Left border accent by type */
.tool-card.type-tool-call {
  border-left: 3px solid #8B5CF6;
}

.tool-card.type-tool-result {
  border-left: 3px solid #10B981;
}

.tool-card.type-error {
  border-left: 3px solid #EF4444;
}

.tool-card.type-info {
  border-left: 3px solid #3B82F6;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(6px); }
  to { opacity: 1; transform: translateY(0); }
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-bottom: 1px solid var(--color-border, #f3f4f6);
  gap: 10px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Type badge - modern pill style */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 10px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 20px;
  text-transform: uppercase;
  letter-spacing: 0.3px;
  white-space: nowrap;
}

.type-icon {
  display: flex;
  align-items: center;
}

.type-badge.badge-call {
  background: rgba(139, 92, 246, 0.1);
  color: #7C3AED;
}

.type-badge.badge-result {
  background: rgba(16, 185, 129, 0.1);
  color: #059669;
}

.type-badge.badge-error {
  background: rgba(239, 68, 68, 0.1);
  color: #DC2626;
}

.type-badge.badge-info {
  background: rgba(59, 130, 246, 0.1);
  color: #2563EB;
}

.type-badge.badge-default {
  background: #f3f4f6;
  color: #64748B;
}

.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 20px;
  letter-spacing: 0.2px;
  background: #f8fafc;
  color: #475569;
}

.agent-badge.supervisor {
  background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%);
  color: #4338CA;
}

.agent-badge.analyst {
  background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
  color: #047857;
}

.agent-badge.system {
  background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
  color: #1D4ED8;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-left: auto;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text, #1f2937);
}

.time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #9CA3AF;
  font-family: 'SF Mono', Monaco, Consolas, monospace;
  white-space: nowrap;
}

.token-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 600;
  color: #7C3AED;
  background: rgba(139, 92, 246, 0.08);
  padding: 3px 8px;
  border-radius: 20px;
  white-space: nowrap;
  cursor: default;
}

.token-badge svg {
  flex-shrink: 0;
}

.tool-body {
  padding: 12px 14px;
  font-size: 13px;
}

/* Message boxes */
.message-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 8px;
}

.message-box.info {
  background: rgba(59, 130, 246, 0.06);
}

.message-box.info .message-icon {
  color: #3B82F6;
}

.message-box.error {
  background: rgba(239, 68, 68, 0.06);
}

.message-box.error .message-icon {
  color: #EF4444;
}

.message-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.message-content {
  color: var(--color-text, #374151);
  line-height: 1.5;
}

/* Tool sections */
.tool-call-section,
.tool-result-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* Code blocks */
.code-block {
  border-radius: 8px;
  overflow: hidden;
  border: 1px solid #e5e7eb;
}

.code-header {
  padding: 6px 10px;
  background: #1E293B;
  border-bottom: 1px solid #334155;
}

.code-lang {
  font-size: 10px;
  font-weight: 600;
  color: #94A3B8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* Simulation block */
.simulation-block {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: linear-gradient(135deg, #F5F3FF 0%, #EDE9FE 100%);
  border: 1px solid #DDD6FE;
  border-radius: 8px;
}

.sim-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #7C3AED;
  color: white;
  border-radius: 10px;
  flex-shrink: 0;
}

.sim-details {
  flex: 1;
}

.sim-title {
  font-weight: 600;
  color: #7C3AED;
  font-size: 13px;
  margin-bottom: 4px;
}

.sim-params {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #6B7280;
}

.sim-params strong {
  color: #374151;
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
  color: var(--color-primary, #7C3AED);
  font-weight: 500;
  padding: 4px 0;
  transition: color 0.2s;
}

.expand-toggle:hover {
  color: #5B21B6;
}

.toggle-icon {
  display: flex;
  align-items: center;
  transition: transform 0.2s;
}

.toggle-icon.rotated {
  transform: rotate(90deg);
}

.raw-json {
  margin-top: 8px;
  background: #1E293B;
  color: #E2E8F0;
  padding: 12px;
  border-radius: 8px;
  font-family: 'SF Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  border: 1px solid #334155;
}

/* Expand transition */
.expand-enter-active,
.expand-leave-active {
  transition: all 0.2s ease;
}

.expand-enter-from,
.expand-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Result output */
.result-output {
  padding: 10px 12px;
  background: #F0FDF4;
  border: 1px solid #BBF7D0;
  border-radius: 8px;
  color: #059669;
  font-weight: 500;
  font-size: 12px;
}

.result-output.python {
  background: #0F172A;
  color: #7DD3FC;
  font-family: 'SF Mono', ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.5;
  padding: 12px;
  border-radius: 8px;
}

.result-output.python pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
