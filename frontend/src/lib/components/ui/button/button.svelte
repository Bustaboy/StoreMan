<script lang="ts">
  import { cn } from '$lib/utils';

  type Variant = 'default' | 'ghost';

  let {
    class: className,
    variant = 'default',
    type = 'button',
    ...rest
  }: {
    class?: string;
    variant?: Variant;
    type?: 'button' | 'submit' | 'reset';
  } = $props();

  const variants: Record<Variant, string> = {
    default: 'bg-primary text-primary-foreground hover:opacity-90',
    ghost: 'bg-transparent hover:bg-muted'
  };
</script>

<button
  {type}
  class={cn(
    'inline-flex h-9 items-center justify-center rounded-md px-4 text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50',
    variants[variant],
    className
  )}
  {...rest}
>
  {@render rest.children?.()}
</button>
