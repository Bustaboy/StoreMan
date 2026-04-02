import { writable } from 'svelte/store';

export type PageId = 'dashboard' | 'inventory' | 'work-orders' | 'planning' | 'mobilization';

export type NavItem = {
  id: PageId;
  label: string;
};

export const navItems: NavItem[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'inventory', label: 'Inventory' },
  { id: 'work-orders', label: 'Work Orders' },
  { id: 'planning', label: 'Planning' },
  { id: 'mobilization', label: 'Mobilization' }
];

export const currentPage = writable<PageId>('dashboard');
