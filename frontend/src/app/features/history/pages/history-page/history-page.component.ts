import { Component, OnInit, computed, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { HistoryApiService } from '../../services/history-api.service';
import { HistoryItem } from '../../models/history.model';
import { ModalComponent } from '../../../../shared/components/modal/modal.component';
import { SkeletonComponent } from '../../../../shared/components/skeleton/skeleton.component';

export type HistoryRangeId = 'all' | '24h' | '7d' | '30d';
export type HistorySortId = 'newest' | 'oldest';

/** Time-range filter windows, in ms. `all` is absent on purpose — a missing entry
 * reads as "no window", which is exactly the unfiltered case. */
const RANGE_MS: Partial<Record<HistoryRangeId, number>> = {
  '24h': 24 * 3600_000,
  '7d': 7 * 24 * 3600_000,
  '30d': 30 * 24 * 3600_000,
};

const PAGE_SIZE = 6;

/** Midnight of the day `iso` falls on, so day boundaries (not 24h spans) drive
 * "Today" / "Yesterday" — 11pm and 1am are different days, 2 hours apart. */
function startOfDay(date: Date): number {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate()).getTime();
}

function calendarDaysAgo(iso: string): number {
  return Math.round((startOfDay(new Date()) - startOfDay(new Date(iso))) / 86_400_000);
}

/** Day 7 (P1.7): real per-user history from Spring Boot's GET /api/chat/history, with
 * client-side search, restore (reopens the conversation on the Chat page under its
 * original session id) and delete — see docs/api_contracts.md. */
@Component({
  selector: 'app-history-page',
  standalone: true,
  imports: [DatePipe, FormsModule, ModalComponent, SkeletonComponent],
  templateUrl: './history-page.component.html',
  styleUrl: './history-page.component.scss',
})
export class HistoryPageComponent implements OnInit {
  readonly items = signal<HistoryItem[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal<string | null>(null);
  readonly searchTerm = signal('');
  readonly range = signal<HistoryRangeId>('all');
  readonly sort = signal<HistorySortId>('newest');
  readonly page = signal(1);
  readonly pendingDelete = signal<HistoryItem | null>(null);

  readonly pageSize = PAGE_SIZE;
  readonly skeletonRows = [0, 1, 2, 3];
  readonly ranges: ReadonlyArray<{ id: HistoryRangeId; label: string }> = [
    { id: 'all', label: 'All time' },
    { id: '24h', label: 'Today' },
    { id: '7d', label: '7 days' },
    { id: '30d', label: '30 days' },
  ];

  readonly filteredItems = computed(() => {
    const term = this.searchTerm().trim().toLowerCase();
    const window = RANGE_MS[this.range()];
    const cutoff = window ? Date.now() - window : 0;
    const newestFirst = this.sort() === 'newest';

    return this.items()
      .filter((item) => Date.parse(item.timestamp) >= cutoff)
      .filter(
        (item) =>
          !term ||
          item.question.toLowerCase().includes(term) ||
          item.answerSummary.toLowerCase().includes(term),
      )
      .sort((a, b) => {
        const delta = Date.parse(a.timestamp) - Date.parse(b.timestamp);
        return newestFirst ? -delta : delta;
      });
  });

  readonly pageCount = computed(() => Math.max(1, Math.ceil(this.filteredItems().length / PAGE_SIZE)));

  /** Clamped rather than corrected via an effect: filtering down to fewer pages must
   * never leave the view stranded on a page that no longer exists. */
  readonly currentPage = computed(() => Math.min(this.page(), this.pageCount()));

  readonly pagedItems = computed(() => {
    const start = (this.currentPage() - 1) * PAGE_SIZE;
    return this.filteredItems().slice(start, start + PAGE_SIZE);
  });

  /** Consecutive runs of same-day-bucket items, so the list carries date headers
   * without the template having to compare neighbours itself. */
  readonly pagedGroups = computed(() => {
    const groups: { label: string; items: HistoryItem[] }[] = [];
    for (const item of this.pagedItems()) {
      const label = this.groupLabel(item.timestamp);
      const last = groups.at(-1);
      if (last?.label === label) {
        last.items.push(item);
      } else {
        groups.push({ label, items: [item] });
      }
    }
    return groups;
  });

  /** At most five page buttons, windowed around the current page. */
  readonly pageNumbers = computed(() => {
    const total = this.pageCount();
    const start = Math.max(1, Math.min(this.currentPage() - 2, total - 4));
    return Array.from({ length: Math.min(5, total) }, (_, i) => start + i);
  });

  readonly rangeStart = computed(() => (this.currentPage() - 1) * PAGE_SIZE + 1);
  readonly rangeEnd = computed(() => Math.min(this.currentPage() * PAGE_SIZE, this.filteredItems().length));
  readonly hasActiveFilters = computed(() => this.searchTerm().trim().length > 0 || this.range() !== 'all');

  constructor(
    private readonly historyApi: HistoryApiService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.load();
  }

  refresh(): void {
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
    this.page.set(1);
  }

  setRange(id: HistoryRangeId): void {
    this.range.set(id);
    this.page.set(1);
  }

  toggleSort(): void {
    this.sort.update((current) => (current === 'newest' ? 'oldest' : 'newest'));
    this.page.set(1);
  }

  clearFilters(): void {
    this.searchTerm.set('');
    this.range.set('all');
    this.page.set(1);
  }

  goToPage(page: number): void {
    this.page.set(Math.min(Math.max(1, page), this.pageCount()));
  }

  /** Reopens this conversation on the Chat page, which restores every turn and continues
   * sending new messages under the same session id rather than starting a new one. */
  restore(item: HistoryItem): void {
    this.router.navigate(['/chat'], { queryParams: { sessionId: item.sessionId } });
  }

  startChat(): void {
    this.router.navigate(['/chat']);
  }

  confirmRemove(item: HistoryItem): void {
    this.pendingDelete.set(item);
  }

  cancelRemove(): void {
    this.pendingDelete.set(null);
  }

  remove(): void {
    const item = this.pendingDelete();
    if (!item) {
      return;
    }
    this.pendingDelete.set(null);
    this.historyApi.deleteHistory(item.id).subscribe({
      next: () => this.items.update((items) => items.filter((i) => i.id !== item.id)),
      error: (err: unknown) => {
        this.errorMessage.set(err instanceof Error ? err.message : 'Unable to delete that conversation.');
      },
    });
  }

  /** Short, scannable age — the exact instant stays available as the `title`/`datetime`. */
  relativeTime(iso: string): string {
    const minutes = Math.floor((Date.now() - Date.parse(iso)) / 60_000);
    if (minutes < 1) {
      return 'Just now';
    }
    if (minutes < 60) {
      return `${minutes} min ago`;
    }
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
      return `${hours} hr ago`;
    }
    const days = calendarDaysAgo(iso);
    if (days <= 1) {
      return 'Yesterday';
    }
    if (days < 7) {
      return `${days} days ago`;
    }
    return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  }

  private groupLabel(iso: string): string {
    const days = calendarDaysAgo(iso);
    if (days <= 0) {
      return 'Today';
    }
    if (days === 1) {
      return 'Yesterday';
    }
    if (days < 7) {
      return 'Earlier this week';
    }
    if (days < 30) {
      return 'Earlier this month';
    }
    return 'Older';
  }
}
