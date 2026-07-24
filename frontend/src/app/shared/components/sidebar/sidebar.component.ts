import { Component, OnInit, computed, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { BackendHealthService } from '../../../core/services/backend-health.service';
import { AuthService } from '../../../core/services/auth.service';

type BackendStatus = 'checking' | 'up' | 'unreachable';

/** Icon keys resolve to inline Lucide path data in the template — see the note there. */
export interface NavItem {
  path: string;
  label: string;
  icon: 'chat' | 'history' | 'audit';
}

const COLLAPSED_KEY = 'nexchain.sidebar.collapsed';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit {
  readonly backendStatus = signal<BackendStatus>('checking');
  readonly collapsed = signal(localStorage.getItem(COLLAPSED_KEY) === 'true');

  /** Drives the sliding indicator's offset. Reported by RouterLinkActive rather
   * than derived from Router.url — the directive already resolves which link
   * owns the route, so re-deriving it here would be a second source of truth. */
  readonly activeIndex = signal(-1);

  /** One source of truth for the nav: the template renders it, and the indicator
   * indexes into it. Audit is admin-only, so the list — and therefore the
   * indicator's travel — is shorter for non-admins. */
  readonly navItems = computed<NavItem[]>(() => {
    const items: NavItem[] = [
      { path: '/chat', label: 'Chat', icon: 'chat' },
      { path: '/history', label: 'History', icon: 'history' },
    ];
    if (this.authService.currentUser()?.role === 'ADMIN') {
      items.push({ path: '/audit', label: 'Audit', icon: 'audit' });
    }
    return items;
  });

  readonly initial = computed(() =>
    (this.authService.currentUser()?.username ?? '?').charAt(0).toUpperCase(),
  );

  readonly statusLabel = computed(() => {
    switch (this.backendStatus()) {
      case 'up':
        return 'Connected';
      case 'unreachable':
        return 'Unreachable';
      default:
        return 'Checking…';
    }
  });

  constructor(
    private readonly backendHealthService: BackendHealthService,
    readonly authService: AuthService,
  ) {}

  ngOnInit(): void {
    this.backendHealthService.checkHealth().subscribe({
      next: () => this.backendStatus.set('up'),
      error: () => this.backendStatus.set('unreachable'),
    });
  }

  /** Only the becoming-active link is acted on: the outgoing link also fires,
   * with false, and the two orders are not guaranteed. */
  onActiveChange(index: number, isActive: boolean): void {
    if (isActive) {
      this.activeIndex.set(index);
    }
  }

  toggleCollapsed(): void {
    this.collapsed.update((value) => !value);
    localStorage.setItem(COLLAPSED_KEY, String(this.collapsed()));
  }

  onLogout(): void {
    this.authService.logout();
  }
}
