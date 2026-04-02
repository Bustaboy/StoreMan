<script lang="ts">
  import { onMount } from 'svelte';
  import Button from '$lib/components/ui/button/button.svelte';

  let theme = $state<'light' | 'dark'>('light');

  function applyTheme(next: 'light' | 'dark') {
    theme = next;
    document.documentElement.classList.toggle('dark', next === 'dark');
    localStorage.setItem('theme', next);
  }

  onMount(() => {
    const saved = localStorage.getItem('theme');
    const savedTheme = saved === 'dark' || saved === 'light' ? saved : null;
    const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    applyTheme(savedTheme ?? (prefersDark ? 'dark' : 'light'));
  });
</script>

<Button variant="ghost" onclick={() => applyTheme(theme === 'dark' ? 'light' : 'dark')}>
  {theme === 'dark' ? '☀️ Light' : '🌙 Dark'}
</Button>
