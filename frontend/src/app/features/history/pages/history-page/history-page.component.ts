import { Component } from '@angular/core';

interface HistoryItem {
  question: string;
  timestamp: string;
  summary: string;
}

@Component({
  selector: 'app-history-page',
  standalone: true,
  imports: [],
  templateUrl: './history-page.component.html',
  styleUrl: './history-page.component.scss',
})
export class HistoryPageComponent {
  readonly items: HistoryItem[] = [
    {
      question: 'Where is order SO-45892? Why is it delayed?',
      timestamp: '2026-07-06 14:32',
      summary: 'Customs hold at Chennai Port — SLA breached, 6-day delay.',
    },
    {
      question: 'Is SKU-1001 in stock?',
      timestamp: '2026-07-06 11:05',
      summary: '240 units on hand at Chennai warehouse.',
    },
    {
      question: 'Show delayed orders from Chennai warehouse.',
      timestamp: '2026-07-05 09:47',
      summary: '4 orders currently delayed.',
    },
  ];
}
