import { Component, Input } from '@angular/core';

/** Renders the recommended-actions list. Self-hides when empty (P1.9). */
@Component({
  selector: 'app-recommendations-card',
  standalone: true,
  imports: [],
  templateUrl: './recommendations-card.component.html',
  styleUrl: './recommendations-card.component.scss',
})
export class RecommendationsCardComponent {
  @Input() actions: string[] = [];
}
