import { Component, Input } from '@angular/core';

export type BadgeStatus = 'breached' | 'na' | 'success' | 'danger';

@Component({
  selector: 'app-badge',
  standalone: true,
  imports: [],
  templateUrl: './badge.component.html',
  styleUrl: './badge.component.scss',
})
export class BadgeComponent {
  @Input() status: BadgeStatus = 'na';
}
