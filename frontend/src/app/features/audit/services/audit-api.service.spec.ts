import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { AuditApiService } from './audit-api.service';
import { AuditEntry } from '../models/audit.model';

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

    const mockEntries: AuditEntry[] = [
      {
        auditId: 1,
        traceId: 'trace-1',
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
      },
    ];
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
});
