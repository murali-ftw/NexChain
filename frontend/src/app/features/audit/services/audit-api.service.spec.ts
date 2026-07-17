import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { AuditApiService } from './audit-api.service';
import { AuditEntry } from '../models/audit.model';

const MOCK_ENTRY: AuditEntry = {
  auditId: 1,
  traceId: 'trace-1',
  sessionId: 'sess-1',
  timestamp: new Date().toISOString(),
  user: 'demo-user',
  rawQuestion: 'Where is order SO-45892?',
  detectedIntent: ['order_status'],
  agentsInvoked: ['text_to_sql_agent'],
  generatedSql: null,
  apiCalls: [{ endpoint: '/api/shipment/status/SO-45892', statusCode: 200, latencyMs: 340 }],
  kbSources: [],
  slaResult: 'Breached',
  status: 'SUCCESS',
  warnings: [],
};

describe('AuditApiService', () => {
  let service: AuditApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(AuditApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('gets the audit log from /api/audit', () => {
    let result: AuditEntry[] | undefined;
    service.getAuditLog().subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/audit`);
    expect(req.request.method).toBe('GET');

    const mockEntries: AuditEntry[] = [MOCK_ENTRY];
    req.flush(mockEntries);

    expect(result).toEqual(mockEntries);
  });

  it('falls back to a generic message when the backend is unreachable', () => {
    let caught: unknown;
    service.getAuditLog().subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/audit`);
    req.error(new ProgressEvent('error'));

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('Unable to load the audit log. Please try again.');
  });

  it('gets one audit entry from /api/audit/{id}', () => {
    let result: AuditEntry | undefined;
    service.getAuditEntry(1).subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/audit/1`);
    expect(req.request.method).toBe('GET');
    req.flush(MOCK_ENTRY);

    expect(result).toEqual(MOCK_ENTRY);
  });

  it('falls back to a not-found message when audit detail 404s without a backend message', () => {
    let caught: unknown;
    service.getAuditEntry(999).subscribe({ error: (e) => (caught = e) });

    httpMock.expectOne(`${environment.apiBaseUrl}/api/audit/999`).flush(null, { status: 404, statusText: 'Not Found' });

    expect((caught as Error).message).toBe('That audit entry could not be found.');
  });

  it('gets one page of the audit log and reads the total count from X-Total-Count', () => {
    let result: { items: AuditEntry[]; totalCount: number } | undefined;
    service.getAuditLogPage(0, 2).subscribe((r) => (result = r));

    const req = httpMock.expectOne(
      (r) => r.url === `${environment.apiBaseUrl}/api/audit` && r.params.get('page') === '0' && r.params.get('size') === '2',
    );
    expect(req.request.method).toBe('GET');
    req.flush([MOCK_ENTRY], { headers: { 'X-Total-Count': '5' } });

    expect(result?.items).toEqual([MOCK_ENTRY]);
    expect(result?.totalCount).toBe(5);
  });
});
