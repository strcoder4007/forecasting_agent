<template>
  <div class="app">
    <header class="header">
      <div class="header-content">
        <nav class="nav">
          <router-link to="/run" class="nav-link" :class="{ active: $route.path === '/run' }">
            Chat
          </router-link>
          <router-link to="/history" class="nav-link" :class="{ active: $route.path === '/history' }">
            History
          </router-link>
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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

:root {
  --color-primary: #7C3AED;
  --color-primary-light: #A78BFA;
  --color-cta: #06B6D4;
  --color-bg: #FAF5FF;
  --color-bg-card: #FFFFFF;
  --color-text: #1E1B4B;
  --color-text-muted: #6B7280;
  --color-border: #E5E7EB;
  --shadow-sm: 0 1px 2px rgba(0, 0, 0, 0.05);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  --radius-sm: 8px;
  --radius-md: 12px;
  --radius-lg: 16px;
  --transition: all 0.2s ease;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: var(--color-bg);
  color: var(--color-text);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: transparent;
  padding: 16px 24px;
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-content {
  max-width: 100%;
  margin: 0 auto;
  display: flex;
  align-items: center;
  justify-content: flex-end; /* align nav to the right if there's no logo, or center, but user said 'only chat and history buttons' */
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 10px;
}

.logo-icon {
  width: 22px;
  height: 22px;
  color: var(--color-primary);
}

.logo {
  font-size: 16px;
  font-weight: 600;
  color: var(--color-text);
  letter-spacing: -0.3px;
}

.nav {
  display: flex;
  gap: 12px;
}

.nav-link {
  text-decoration: none;
  color: var(--color-text-muted);
  font-size: 14px;
  font-weight: 600;
  padding: 10px 20px;
  border-radius: 30px; /* rounded pill shape */
  background: var(--color-bg-card);
  box-shadow: var(--shadow-sm);
  transition: var(--transition);
  border: 1px solid var(--color-border);
}

.nav-link:hover {
  color: var(--color-text);
  box-shadow: var(--shadow-md);
  transform: translateY(-1px);
}

.nav-link.active {
  color: white;
  background: var(--color-primary);
  border-color: var(--color-primary);
  box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3);
}

.main {
  flex: 1;
  max-width: 100%;
  width: 100%;
  margin: 0 auto;
  padding: 0 24px;
}

/* Button styles */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 24px;
  border-radius: var(--radius-sm);
  font-size: 14px;
  font-weight: 600;
  text-decoration: none;
  transition: var(--transition);
  border: none;
  cursor: pointer;
}

.btn-primary {
  background: var(--color-primary);
  color: white;
}

.btn-primary:hover {
  background: #6D28D9;
  transform: translateY(-1px);
}

.btn-secondary {
  background: var(--color-bg-card);
  color: var(--color-text);
  border: 1px solid var(--color-border);
}

.btn-secondary:hover {
  border-color: var(--color-primary-light);
  background: rgba(124, 58, 237, 0.02);
}

/* Card styles */
.card {
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  padding: 20px;
  box-shadow: var(--shadow-sm);
}
</style>