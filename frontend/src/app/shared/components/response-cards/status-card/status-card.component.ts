import { Component, Input } from '@angular/core';

/** Renders Order Status. Self-hides when the field is absent, so callers can
 * include it unconditionally (P1.9 — see docs/api_contracts.md). */
@Component({
  selector: 'app-status-card',
  standalone: true,
  imports: [],
  templateUrl: './status-card.component.html',
  styleUrl: './status-card.component.scss',
})
export class StatusCardComponent {
  @Input() orderStatus: string | null = null;
}
