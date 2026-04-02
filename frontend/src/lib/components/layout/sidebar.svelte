<script lang="ts">
  import { currentPage, navItems, type PageId } from '$lib/stores/navigation';

  function goTo(pageId: PageId) {
    currentPage.set(pageId);
  }
</script>

<aside class="w-64 border-r border-border bg-muted/40 p-4">
  <h1 class="mb-6 text-lg font-semibold">TitanWMS</h1>
  <nav class="space-y-1">
    {#each navItems as item}
      <button
        class="w-full rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted {$currentPage === item.id
          ? 'bg-background font-medium'
          : 'text-muted-foreground'}"
        onclick={() => goTo(item.id)}
      >
        {item.label}
      </button>
    {/each}
  </nav>
</aside>
