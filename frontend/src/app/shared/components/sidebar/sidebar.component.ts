import { Component, OnInit, signal } from '@angular/core';
import { RouterLink, RouterLinkActive } from '@angular/router';
import { BackendHealthService } from '../../../core/services/backend-health.service';
import { AuthService } from '../../../core/services/auth.service';

type BackendStatus = 'checking' | 'up' | 'unreachable';

@Component({
  selector: 'app-sidebar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './sidebar.component.html',
  styleUrl: './sidebar.component.scss',
})
export class SidebarComponent implements OnInit {
  readonly backendStatus = signal<BackendStatus>('checking');

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

  onLogout(): void {
    this.authService.logout();
  }
}
