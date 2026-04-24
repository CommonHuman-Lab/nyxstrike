export type Page =
  | 'dashboard'
  | 'settings'
  | 'help'
  | 'logs'
  | 'run'
  | 'tasks'
  | 'tools'
  | 'plugins'
  | 'reports'
  | 'sessions'
  | 'session-detail';

const VALID_PAGES = new Set<Page>([
  'dashboard',
  'settings',
  'help',
  'logs',
  'run',
  'tasks',
  'tools',
  'plugins',
  'reports',
  'sessions',
  'session-detail',
]);

export function routeFromHash(): { page: Page; sessionId: string | null } {
  const hash = window.location.hash.replace(/^#\/?/, '');
  if (hash.startsWith('sessions/')) {
    const sessionId = hash.slice('sessions/'.length);
    return { page: 'session-detail', sessionId: sessionId || null };
  }

  return {
    page: VALID_PAGES.has(hash as Page) ? (hash as Page) : 'dashboard',
    sessionId: null,
  };
}
