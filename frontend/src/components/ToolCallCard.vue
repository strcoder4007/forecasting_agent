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
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  margin-bottom: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
  animation: slideIn 0.3s ease-out forwards;
  transition: all 0.2s ease;
}

.tool-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
}

/* Card type backgrounds - subtle tinted backgrounds */
.tool-card.type-tool-call {
  border-color: #DDD6FE;
  background: linear-gradient(135deg, #FAFAFF 0%, #F5F3FF 100%);
}

.tool-card.type-tool-result {
  border-color: #A7F3D0;
  background: linear-gradient(135deg, #FAFAFF 0%, #F0FDF4 100%);
}

.tool-card.type-error {
  border-color: #FECACA;
  background: linear-gradient(135deg, #FFFAFA 0%, #FEF2F2 100%);
}

.tool-card.type-info {
  border-color: #BAE6FD;
  background: linear-gradient(135deg, #FAFAFF 0%, #F0F9FF 100%);
}

.tool-card.type-default {
  border-color: #E5E7EB;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}

.tool-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: linear-gradient(to bottom, rgba(255,255,255,0.8), rgba(248,248,248,0.8));
  border-bottom: 1px solid #E5E7EB;
  gap: 12px;
  flex-wrap: wrap;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* Type badge - primary color indicator */
.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 10px;
  font-weight: 700;
  padding: 4px 8px;
  border-radius: 4px;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  white-space: nowrap;
}

.type-icon {
  display: flex;
  align-items: center;
}

.type-badge.badge-call {
  background: #EDE9FE;
  color: #7C3AED;
  border: 1px solid #DDD6FE;
}

.type-badge.badge-result {
  background: #D1FAE5;
  color: #059669;
  border: 1px solid #A7F3D0;
}

.type-badge.badge-error {
  background: #FEE2E2;
  color: #DC2626;
  border: 1px solid #FECACA;
}

.type-badge.badge-info {
  background: #E0F2FE;
  color: #0284C7;
  border: 1px solid #BAE6FD;
}

.type-badge.badge-default {
  background: #F1F5F9;
  color: #64748B;
  border: 1px solid #E2E8F0;
}

.agent-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  font-weight: 600;
  padding: 3px 8px;
  border-radius: 4px;
  letter-spacing: 0.3px;
}

.badge-icon {
  font-size: 10px;
}

.agent-badge.supervisor {
  background: linear-gradient(135deg, #E0E7FF 0%, #C7D2FE 100%);
  color: #4338CA;
}

.agent-badge.analyst {
  background: linear-gradient(135deg, #D1FAE5 0%, #A7F3D0 100%);
  color: #047857;
}

.agent-badge.system {
  background: linear-gradient(135deg, #DBEAFE 0%, #BFDBFE 100%);
  color: #1D4ED8;
}

.tool-divider {
  color: #9CA3AF;
  font-size: 12px;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
}

.tool-name {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
}

.time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: var(--color-text-muted);
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
  background: linear-gradient(135deg, #EDE9FE 0%, #DDD6FE 100%);
  padding: 3px 8px;
  border-radius: 4px;
  border: 1px solid #C4B5FD;
  white-space: nowrap;
  cursor: default;
}

.token-badge svg {
  flex-shrink: 0;
}

.tool-body {
  padding: 14px;
  font-size: 13px;
}

/* Message boxes - integrated into card type styling */
.message-box {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 10px 12px;
  border-radius: 6px;
}

.message-box.info {
  background: rgba(224, 242, 254, 0.5);
  border: 1px solid #BAE6FD;
}

.message-box.info .message-icon {
  color: #0284C7;
}

.message-box.error {
  background: rgba(254, 226, 226, 0.5);
  border: 1px solid #FECACA;
}

.message-box.error .message-icon {
  color: #DC2626;
}

.message-icon {
  flex-shrink: 0;
  margin-top: 1px;
}

.message-content {
  color: var(--color-text);
  line-height: 1.5;
}

/* Tool call section */
.tool-call-section,
.tool-result-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

/* Code blocks */
.code-block {
  border-radius: 6px;
  overflow: hidden;
  border: 1px solid #E5E7EB;
}

.code-header {
  padding: 6px 10px;
  background: #1E1E1E;
  border-bottom: 1px solid #2D2D2D;
}

.code-lang {
  font-size: 10px;
  font-weight: 600;
  color: #9CA3AF;
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
  border-radius: 6px;
}

.sim-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #7C3AED;
  color: white;
  border-radius: 8px;
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
  color: var(--color-primary);
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
  background: #1E1E1E;
  color: #E5E7EB;
  padding: 12px;
  border-radius: 6px;
  font-family: 'SF Mono', ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.5;
  overflow-x: auto;
  border: 1px solid #374151;
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
  border-radius: 6px;
  color: #059669;
  font-weight: 500;
  font-size: 12px;
}

.result-output.python {
  background: #1E1E1E;
  color: #A5D6FF;
  font-family: 'SF Mono', ui-monospace, SFMono-Regular, Monaco, Consolas, monospace;
  font-size: 11px;
  line-height: 1.5;
  padding: 12px;
  border-left: 3px solid #10B981;
}

.result-output.python pre {
  margin: 0;
  white-space: pre-wrap;
  word-break: break-all;
}
</style>
