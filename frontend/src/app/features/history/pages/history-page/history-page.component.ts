import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { HistoryApiService } from '../../services/history-api.service';
import { HistoryItem } from '../../models/history.model';

/** Day 5 (P1.5): fetches real history from Spring Boot's GET /api/chat/history —
 * see docs/api_contracts.md. Backend data is a fixed mock today; no persistence
 * until P1.7 (Day 7), so nothing here writes new entries. */
@Component({
  selector: 'app-history-page',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './history-page.component.html',
  styleUrl: './history-page.component.scss',
})
export class HistoryPageComponent implements OnInit {
  readonly items = signal<HistoryItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal<string | null>(null);

  constructor(private readonly historyApi: HistoryApiService) {}

  ngOnInit(): void {
    this.historyApi.getHistory().subscribe({
      next: (items) => {
        this.items.set(items);
        this.isLoading.set(false);
      },
      error: (err: unknown) => {
        this.errorMessage.set(
          err instanceof Error ? err.message : 'Unable to load query history. Please try again.',
        );
        this.isLoading.set(false);
      },
    });
  }
}
