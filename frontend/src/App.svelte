<script lang="ts">
  import Sidebar from '$lib/components/layout/sidebar.svelte';
  import ThemeToggle from '$lib/components/ui/theme-toggle.svelte';
  import Inventory from '$lib/pages/Inventory.svelte';
  import { healthCheck } from '$lib/api';
  import { currentPage, navItems, type PageId } from '$lib/stores/navigation';

  let backendStatus = $state<'checking' | 'online' | 'offline'>('checking');
  let backendMessage = $state('Checking backend connection...');

  const pageDescriptions: Record<PageId, string> = {
    dashboard: 'NDT warehouse operations at a glance',
    inventory: 'Track stock levels and item movements',
    'work-orders': 'Manage order queue and assignment',
    planning: 'Plan inbound and outbound logistics',
    mobilization: 'Coordinate field mobilization readiness'
  };

  $effect(() => {
    void (async () => {
      backendStatus = 'checking';
      backendMessage = 'Checking backend connection...';

      const result = await healthCheck();

      if (result.ok) {
        backendStatus = 'online';
        backendMessage = result.data?.status ?? 'Backend is reachable';
        return;
      }

      backendStatus = 'offline';
      backendMessage = result.error ?? 'Unable to connect to backend at http://localhost:8000';
    })();
  });

  const activePage = $derived.by(() => navItems.find((item) => item.id === $currentPage) ?? navItems[0]);
</script>

<div class="flex h-full">
  <Sidebar />

  <main class="flex-1 p-6">
    <div class="mb-8 flex items-center justify-between">
      <div>
        <h2 class="text-2xl font-semibold">{activePage.label}</h2>
        <p class="text-sm text-muted-foreground">{pageDescriptions[activePage.id]}</p>
      </div>
      <ThemeToggle />
    </div>

    {#if activePage.id === 'inventory'}
      <Inventory />
    {:else}
      <section class="rounded-lg border border-border bg-background p-4 shadow-sm">
        <h3 class="mb-2 text-sm font-medium">Backend Health</h3>
        <p class="text-sm">
          <span
            class="mr-2 inline-flex h-2.5 w-2.5 rounded-full {backendStatus === 'online'
              ? 'bg-green-500'
              : backendStatus === 'offline'
                ? 'bg-red-500'
                : 'bg-yellow-500 animate-pulse'}"
          ></span>
          {backendStatus === 'checking' ? 'Loading backend status…' : backendMessage}
        </p>
      </section>
    {/if}
  </main>
</div>
