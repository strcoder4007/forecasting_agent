<template>
  <div class="app">
    <header class="header">
      <div class="header-content">
        <h1 class="logo">Demand Forecasting Agent</h1>
        <nav class="nav">
          <router-link to="/" class="nav-link">Dashboard</router-link>
          <router-link to="/run" class="nav-link">Run Forecast</router-link>
          <router-link to="/results" class="nav-link">Results</router-link>
          <router-link to="/history" class="nav-link">History</router-link>
        </nav>
      </div>
    </header>
    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<script>
export default {
  name: 'App'
}
</script>

<style>
.app {
  min-height: 100vh;
}

.header {
  background: #FFFFFF;
  border-bottom: 1px solid #E2E8F0;
  padding: 16px 24px;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.logo {
  font-size: 20px;
  font-weight: 600;
  color: #2563EB;
}

.nav {
  display: flex;
  gap: 24px;
}

.nav-link {
  text-decoration: none;
  color: #64748B;
  font-size: 14px;
  font-weight: 500;
  padding: 8px 0;
  border-bottom: 2px solid transparent;
  transition: all 0.2s;
}

.nav-link:hover {
  color: #2563EB;
}

.nav-link.router-link-active {
  color: #2563EB;
  border-bottom-color: #2563EB;
}

.main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 24px;
}
</style>
