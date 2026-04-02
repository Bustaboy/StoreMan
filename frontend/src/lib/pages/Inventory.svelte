<script lang="ts">
  import { fetchMaterials, type Material } from '$lib/api';

  type SortKey = 'code' | 'name' | 'category' | 'quantity_on_hand' | 'location';
  type SortDirection = 'asc' | 'desc';

  let loading = $state(true);
  let error = $state<string | null>(null);
  let searchQuery = $state('');
  let materials = $state<Material[]>([]);
  let sortKey = $state<SortKey>('name');
  let sortDirection = $state<SortDirection>('asc');

  let debounceTimer: number | null = null;

  function compareValues(a: Material, b: Material, key: SortKey): number {
    const first = a[key] ?? '';
    const second = b[key] ?? '';

    if (typeof first === 'number' && typeof second === 'number') {
      return first - second;
    }

    return String(first).localeCompare(String(second));
  }

  const sortedMaterials = $derived.by(() => {
    const direction = sortDirection === 'asc' ? 1 : -1;

    return [...materials].sort((a, b) => compareValues(a, b, sortKey) * direction);
  });

  async function loadMaterials(query = '') {
    loading = true;
    error = null;

    const result = await fetchMaterials(query);

    if (!result.ok) {
      materials = [];
      error = result.error ?? 'Unable to load materials';
      loading = false;
      return;
    }

    materials = result.data ?? [];
    loading = false;
  }

  function onSearchInput(value: string) {
    searchQuery = value;

    if (debounceTimer !== null) {
      window.clearTimeout(debounceTimer);
    }

    debounceTimer = window.setTimeout(() => {
      void loadMaterials(searchQuery);
    }, 250);
  }

  function toggleSort(key: SortKey) {
    if (sortKey === key) {
      sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
      return;
    }

    sortKey = key;
    sortDirection = 'asc';
  }

  $effect(() => {
    void loadMaterials();

    return () => {
      if (debounceTimer !== null) {
        window.clearTimeout(debounceTimer);
      }
    };
  });
</script>

<section class="rounded-lg border border-border bg-background p-4 shadow-sm">
  <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h3 class="text-base font-semibold">Materials</h3>
      <p class="text-sm text-muted-foreground">Live inventory list with instant search.</p>
    </div>
    <input
      class="h-9 w-full rounded-md border border-input bg-background px-3 py-1 text-sm shadow-sm outline-none ring-offset-background placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring sm:w-72"
      placeholder="Search code, name, category..."
      value={searchQuery}
      oninput={(event) => onSearchInput((event.currentTarget as HTMLInputElement).value)}
    />
  </div>

  {#if loading}
    <p class="py-8 text-sm text-muted-foreground">Loading materials…</p>
  {:else if error}
    <div class="rounded-md border border-red-300/60 bg-red-50/50 p-3 text-sm text-red-700 dark:border-red-900 dark:bg-red-950/30 dark:text-red-300">
      {error}
    </div>
  {:else}
    <div class="overflow-x-auto rounded-md border border-border">
      <table class="w-full text-sm">
        <thead class="bg-muted/60 text-left">
          <tr>
            <th class="px-3 py-2 font-medium"><button class="hover:underline" onclick={() => toggleSort('code')}>Code</button></th>
            <th class="px-3 py-2 font-medium"><button class="hover:underline" onclick={() => toggleSort('name')}>Name</button></th>
            <th class="px-3 py-2 font-medium"><button class="hover:underline" onclick={() => toggleSort('category')}>Category</button></th>
            <th class="px-3 py-2 font-medium text-right"><button class="hover:underline" onclick={() => toggleSort('quantity_on_hand')}>Qty</button></th>
            <th class="px-3 py-2 font-medium"><button class="hover:underline" onclick={() => toggleSort('location')}>Location</button></th>
          </tr>
        </thead>
        <tbody>
          {#if sortedMaterials.length === 0}
            <tr>
              <td colspan="5" class="px-3 py-8 text-center text-muted-foreground">No materials found.</td>
            </tr>
          {:else}
            {#each sortedMaterials as material (material.id)}
              <tr class="border-t border-border hover:bg-muted/40">
                <td class="px-3 py-2 font-mono text-xs">{material.code}</td>
                <td class="px-3 py-2">{material.name}</td>
                <td class="px-3 py-2 text-muted-foreground">{material.category ?? '—'}</td>
                <td class="px-3 py-2 text-right tabular-nums">{material.quantity_on_hand}</td>
                <td class="px-3 py-2 text-muted-foreground">{material.location ?? '—'}</td>
              </tr>
            {/each}
          {/if}
        </tbody>
      </table>
    </div>
  {/if}
</section>
