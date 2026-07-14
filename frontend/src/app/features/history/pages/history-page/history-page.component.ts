import { Component, OnInit, computed, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HistoryApiService } from '../../services/history-api.service';
import { HistoryItem } from '../../models/history.model';

/** Day 7 (P1.7): real per-user history from Spring Boot's GET /api/chat/history, with
 * client-side search, restore (reopens the conversation on the Chat page under its
 * original session id) and delete — see docs/api_contracts.md. */
@Component({
  selector: 'app-history-page',
  standalone: true,
  imports: [DatePipe, FormsModule],
  templateUrl: './history-page.component.html',
  styleUrl: './history-page.component.scss',
})
export class HistoryPageComponent implements OnInit {
  readonly items = signal<HistoryItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal<string | null>(null);
  readonly searchTerm = signal('');

  readonly filteredItems = computed(() => {
    const term = this.searchTerm().trim().toLowerCase();
    const items = this.items();
    if (!term) {
      return items;
    }
    return items.filter(
      (item) => item.question.toLowerCase().includes(term) || item.answerSummary.toLowerCase().includes(term),
    );
  });

  constructor(
    private readonly historyApi: HistoryApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  private load(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
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

  onSearchTermChange(value: string): void {
    this.searchTerm.set(value);
  }

  /** Reopens this conversation on the Chat page, which restores every turn and continues
   * sending new messages under the same session id rather than starting a new one. */
  restore(item: HistoryItem): void {
    this.router.navigate(['/chat'], { queryParams: { sessionId: item.sessionId } });
  }

  remove(item: HistoryItem): void {
    this.historyApi.deleteHistory(item.id).subscribe({
      next: () => this.items.update((items) => items.filter((i) => i.id !== item.id)),
      error: (err: unknown) => {
        this.errorMessage.set(err instanceof Error ? err.message : 'Unable to delete that conversation.');
      },
    });
  }
}
