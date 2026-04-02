<script lang="ts">
  import Sidebar from '$lib/components/layout/sidebar.svelte';
  import ThemeToggle from '$lib/components/ui/theme-toggle.svelte';
  import { healthCheck } from '$lib/api';

  let backendStatus = $state<'checking' | 'online' | 'offline'>('checking');
  let backendMessage = $state('Checking backend connection...');

  $effect(() => {
    void (async () => {
      try {
        const result = await healthCheck();
        backendStatus = 'online';
        backendMessage = result.status ?? 'Backend is reachable';
      } catch (error) {
        backendStatus = 'offline';
        backendMessage =
          error instanceof Error ? error.message : 'Unable to connect to backend at http://localhost:8000';
      }
    })();
  });
</script>

<div class="flex h-full">
  <Sidebar />

  <main class="flex-1 p-6">
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-semibold">Dashboard</h2>
        <p class="text-sm text-muted-foreground">NDT warehouse operations at a glance</p>
      </div>
      <ThemeToggle />
    </div>

    <section class="rounded-lg border border-border bg-background p-4 shadow-sm">
      <h3 class="mb-2 text-sm font-medium">Backend Health</h3>
      <p class="text-sm">
        <span
          class="mr-2 inline-flex h-2.5 w-2.5 rounded-full {backendStatus === 'online'
            ? 'bg-green-500'
            : backendStatus === 'offline'
              ? 'bg-red-500'
              : 'bg-yellow-500'}"
        ></span>
        {backendMessage}
      </p>
    </section>
  </main>
</div>
