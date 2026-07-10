import { Component, OnInit, signal } from '@angular/core';
import { DatePipe } from '@angular/common';
import { AuditApiService } from '../../services/audit-api.service';
import { AuditEntry } from '../../models/audit.model';

/** Day 5 (P1.5): fetches real audit records from Spring Boot's GET /api/audit —
 * see docs/api_contracts.md. Backend data is a fixed mock today; no persistence
 * or authorization until P1.8 (Day 8). */
@Component({
  selector: 'app-audit-page',
  standalone: true,
  imports: [DatePipe],
  templateUrl: './audit-page.component.html',
  styleUrl: './audit-page.component.scss',
})
export class AuditPageComponent implements OnInit {
  readonly columns = ['Timestamp', 'User', 'Question', 'Intent', 'Agents Invoked', 'SLA Result'];
  readonly entries = signal<AuditEntry[]>([]);
  readonly isLoading = signal(true);
  readonly errorMessage = signal<string | null>(null);

  constructor(private readonly auditApi: AuditApiService) {}

  ngOnInit(): void {
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
}
