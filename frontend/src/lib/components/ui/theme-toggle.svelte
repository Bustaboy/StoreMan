<script lang="ts">
  import Button from '$lib/components/ui/button/button.svelte';

  let theme = $state<'light' | 'dark'>('light');

  function applyTheme(next: 'light' | 'dark') {
    theme = next;
    document.documentElement.classList.toggle('dark', next === 'dark');
    localStorage.setItem('theme', next);
  }

  $effect(() => {
    const saved = localStorage.getItem('theme') as 'light' | 'dark' | null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(saved ?? (prefersDark ? 'dark' : 'light'));
  });
</script>

<Button variant="ghost" on:click={() => applyTheme(theme === 'dark' ? 'light' : 'dark')}>
  {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
</Button>
