import { Component, OnInit, computed, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { AuditApiService } from '../../services/audit-api.service';
import { AuditEntry } from '../../models/audit.model';
import { SlaStatus } from '../../../chat/models/chat.model';
import { BadgeComponent, BadgeStatus } from '../../../../shared/components/badge/badge.component';
import { ModalComponent } from '../../../../shared/components/modal/modal.component';
import { SkeletonComponent } from '../../../../shared/components/skeleton/skeleton.component';
import { TableComponent } from '../../../../shared/components/table/table.component';

/** Day 8 (P1.8): fetches real, persisted audit records from Spring Boot's GET /api/audit
 * — see docs/api_contracts.md. Global admin-facing log: every entry is visible to any
 * caller who reaches this page, not scoped per-user — access itself is restricted to
 * ADMIN, both server-side (SecurityConfig's hasRole("ADMIN")) and, since Day 12,
 * client-side (adminGuard on the /audit route). Adds search, user/date/intent filters,
 * a detail drawer (GET /api/audit/{id}), and refresh. */
@Component({
  selector: 'app-audit-page',
  standalone: true,
  imports: [DatePipe, FormsModule, BadgeComponent, ModalComponent, SkeletonComponent, TableComponent],
  templateUrl: './audit-page.component.html',
  styleUrl: './audit-page.component.scss',
})
export class AuditPageComponent implements OnInit {
  readonly columns = ['Timestamp', 'User', 'Question', 'Intent', 'Agents Invoked', 'SLA Result'];

  /** Placeholder rows for the shimmer skeleton — presentation only. */
  readonly skeletonRows = [0, 1, 2, 3, 4, 5];
  readonly entries = signal<AuditEntry[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal<string | null>(null);

  readonly searchTerm = signal('');
  readonly userFilter = signal('');
  readonly intentFilter = signal('');
  readonly dateFrom = signal('');
  readonly dateTo = signal('');

  readonly selectedEntry = signal<AuditEntry | null>(null);
  readonly isDetailLoading = signal(false);
  readonly detailError = signal<string | null>(null);

  /** Distinct intents actually present in the loaded log, for the filter dropdown —
   * not hardcoded against Person 3's intent taxonomy, since that's their contract to evolve. */
  readonly availableIntents = computed(() => {
    const intents = new Set<string>();
    for (const entry of this.entries()) {
      for (const intent of entry.detectedIntent) {
        intents.add(intent);
      }
    }
    return [...intents].sort();
  });

  readonly filteredEntries = computed(() => {
    const term = this.searchTerm().trim().toLowerCase();
    const user = this.userFilter().trim().toLowerCase();
    const intent = this.intentFilter();
    const from = this.dateFrom();
    const to = this.dateTo();

    return this.entries().filter((entry) => {
      if (term) {
        const haystack = `${entry.rawQuestion} ${entry.traceId} ${entry.user}`.toLowerCase();
        if (!haystack.includes(term)) {
          return false;
        }
      }
      if (user && !entry.user.toLowerCase().includes(user)) {
        return false;
      }
      if (intent && !entry.detectedIntent.includes(intent)) {
        return false;
      }
      const entryDate = entry.timestamp.slice(0, 10);
      if (from && entryDate < from) {
        return false;
      }
      if (to && entryDate > to) {
        return false;
      }
      return true;
    });
  });

  /** Drives the "· filtered" flag in the header count. Presentation only. */
  readonly hasActiveFilters = computed(
    () =>
      this.searchTerm().trim() !== '' ||
      this.userFilter().trim() !== '' ||
      this.intentFilter() !== '' ||
      this.dateFrom() !== '' ||
      this.dateTo() !== '',
  );

  /** Maps the SLA wire value onto the shared <app-badge> palette, so the audit
   * table's SLA column and the chat SLA card tint the same outcome alike. */
  slaBadgeStatus(slaResult: SlaStatus): BadgeStatus {
    switch (slaResult) {
      case 'Breached':
        return 'breached';
      case 'At Risk':
        return 'danger';
      case 'On Time':
        return 'success';
      default:
        return 'na';
    }
  }

  /** Escape hatch from the "no matching records" empty state. */
  clearFilters(): void {
    this.searchTerm.set('');
    this.userFilter.set('');
    this.intentFilter.set('');
    this.dateFrom.set('');
    this.dateTo.set('');
  }

  constructor(private readonly auditApi: AuditApiService) {}

  ngOnInit(): void {
    this.load();
  }

  refresh(): void {
    this.load();
  }

  private load(): void {
    this.isLoading.set(true);
    this.errorMessage.set(null);
    this.auditApi.getAuditLog().subscribe({
      next: (entries) => {
        this.entries.set(entries);
        this.isLoading.set(false);
      },
      error: (err: unknown) => {
        this.errorMessage.set(
          err instanceof Error ? err.message : 'Unable to load the audit log. Please try again.',
        );
        this.isLoading.set(false);
      },
    });
  }

  openDetail(entry: AuditEntry): void {
    this.selectedEntry.set(entry);
    this.isDetailLoading.set(true);
    this.detailError.set(null);
    this.auditApi.getAuditEntry(entry.auditId).subscribe({
      next: (fullEntry) => {
        this.selectedEntry.set(fullEntry);
        this.isDetailLoading.set(false);
      },
      error: (err: unknown) => {
        this.detailError.set(err instanceof Error ? err.message : 'Unable to load this audit entry.');
        this.isDetailLoading.set(false);
      },
    });
  }

  closeDetail(): void {
    this.selectedEntry.set(null);
    this.detailError.set(null);
  }
}
