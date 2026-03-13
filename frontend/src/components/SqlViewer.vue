<template>
  <div class="sql-viewer">
    <div class="sql-header">
      <span class="label">DuckDB SQL</span>
    </div>
    <pre class="sql-code"><code>{{ sql }}</code></pre>
  </div>
</template>

<script>
export default {
  name: 'SqlViewer',
  props: {
    sql: { type: String, required: true }
  }
}
</script>

<style scoped>
.sql-viewer {
  background: #1E1E1E;
  border-radius: var(--radius-sm);
  overflow: hidden;
  margin-top: 8px;
}
.sql-header {
  background: #2D2D2D;
  padding: 4px 12px;
  font-size: 11px;
  color: #A0A0A0;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
.sql-code {
  margin: 0;
  padding: 12px;
  font-size: 12px;
  color: #CE9178;
  white-space: pre-wrap;
  word-break: break-all;
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>