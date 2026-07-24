import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../../environments/environment';
import { AuditEntry } from '../../models/audit.model';
import { AuditPageComponent } from './audit-page.component';

const AUDIT_URL = `${environment.apiBaseUrl}/api/audit`;

const ENTRIES: AuditEntry[] = [
  {
    auditId: 1,
    traceId: 'trace-1',
    sessionId: 'sess-1',
    timestamp: '2026-07-10T10:00:00.000Z',
    user: 'demo-user',
    rawQuestion: 'Where is order SO-45892?',
    detectedIntent: ['MULTI_TOOL_QUERY'],
    agentsInvoked: [],
    generatedSql: null,
    apiCalls: [],
    kbSources: [{ documentName: 'Customs Hold SOP', snippet: null, docId: 3, score: 0.9 }],
    slaResult: 'Breached',
    status: 'SUCCESS',
    warnings: ['Day 4 mock response'],
  },
  {
    auditId: 2,
    traceId: 'trace-2',
    sessionId: 'sess-2',
    timestamp: '2026-07-11T10:00:00.000Z',
    user: 'second-user',
    rawQuestion: 'Is SKU-1001 in stock?',
    detectedIntent: ['DATABASE_QUERY'],
    agentsInvoked: [],
    generatedSql: null,
    apiCalls: [],
    kbSources: [],
    slaResult: 'N/A',
    status: 'SUCCESS',
    warnings: [],
  },
];

describe('AuditPageComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [AuditPageComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('shows the empty state when there are no audit records yet', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush([]);
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Nothing logged yet');
  });

  it('renders every loaded entry', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Where is order SO-45892?');
    expect(text).toContain('Is SKU-1001 in stock?');
  });

  it('search filters across question, user, and trace id', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    fixture.componentInstance.searchTerm.set('SKU');
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('SO-45892');
    expect(text).toContain('Is SKU-1001 in stock?');
  });

  it('user filter narrows to matching entries', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    expect(fixture.componentInstance.filteredEntries().length).toBe(2);
    fixture.componentInstance.userFilter.set('second');
    expect(fixture.componentInstance.filteredEntries().length).toBe(1);
    expect(fixture.componentInstance.filteredEntries()[0].user).toBe('second-user');
  });

  it('intent filter narrows to matching entries', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    expect(fixture.componentInstance.availableIntents()).toEqual(['DATABASE_QUERY', 'MULTI_TOOL_QUERY']);
    fixture.componentInstance.intentFilter.set('DATABASE_QUERY');
    expect(fixture.componentInstance.filteredEntries().length).toBe(1);
    expect(fixture.componentInstance.filteredEntries()[0].auditId).toBe(2);
  });

  it('date range filter narrows to matching entries', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    fixture.componentInstance.dateFrom.set('2026-07-11');
    expect(fixture.componentInstance.filteredEntries().length).toBe(1);
    expect(fixture.componentInstance.filteredEntries()[0].auditId).toBe(2);
  });

  it('opening a row loads the full entry via GET /api/audit/{id}', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    fixture.componentInstance.openDetail(ENTRIES[0]);
    expect(fixture.componentInstance.isDetailLoading()).toBe(true);

    httpMock.expectOne(`${AUDIT_URL}/1`).flush(ENTRIES[0]);
    fixture.detectChanges();

    expect(fixture.componentInstance.isDetailLoading()).toBe(false);
    expect(fixture.componentInstance.selectedEntry()?.auditId).toBe(1);
    expect((fixture.nativeElement as HTMLElement).textContent).toContain('Audit Entry #1');
  });

  it('closing the drawer clears the selected entry', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    fixture.componentInstance.openDetail(ENTRIES[0]);
    httpMock.expectOne(`${AUDIT_URL}/1`).flush(ENTRIES[0]);
    fixture.componentInstance.closeDetail();
    fixture.detectChanges();

    expect(fixture.componentInstance.selectedEntry()).toBeNull();
  });

  it('refresh reloads the audit log', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).flush([ENTRIES[0]]);
    fixture.detectChanges();

    fixture.componentInstance.refresh();
    expect(fixture.componentInstance.isLoading()).toBe(true);
    httpMock.expectOne(AUDIT_URL).flush(ENTRIES);
    fixture.detectChanges();

    expect(fixture.componentInstance.entries().length).toBe(2);
  });

  it('shows an error message when the audit request fails', () => {
    const fixture = TestBed.createComponent(AuditPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(AUDIT_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Unable to load the audit log. Please try again.',
    );
  });
});
