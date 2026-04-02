<script lang="ts">
  const items = ['Dashboard', 'Inventory', 'Work Orders', 'Planning', 'Mobilization'];
</script>

<aside class="w-64 border-r border-border bg-muted/40 p-4">
  <h1 class="mb-6 text-lg font-semibold">TitanWMS</h1>
  <nav class="space-y-1">
    {#each items as item, i}
      <button
        class="w-full rounded-md px-3 py-2 text-left text-sm transition-colors hover:bg-muted {i === 0
          ? 'bg-background font-medium'
          : 'text-muted-foreground'}"
      >
        {item}
      </button>
    {/each}
  </nav>
</aside>
