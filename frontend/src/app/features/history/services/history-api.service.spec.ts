import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { HistoryApiService } from './history-api.service';
import { HistoryDetail, HistoryItem } from '../models/history.model';

describe('HistoryApiService', () => {
  let service: HistoryApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(HistoryApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('gets the history list from /api/chat/history', () => {
    let result: HistoryItem[] | undefined;
    service.getHistory().subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat/history`);
    expect(req.request.method).toBe('GET');

    const mockItems: HistoryItem[] = [
      {
        id: '1',
        question: 'Where is order SO-45892?',
        answerSummary: 'Customs hold at Chennai Port.',
        timestamp: new Date().toISOString(),
        sessionId: 'session-1',
      },
    ];
    req.flush(mockItems);

    expect(result).toEqual(mockItems);
  });

  it('falls back to a generic message when the backend is unreachable', () => {
    let caught: unknown;
    service.getHistory().subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat/history`);
    req.error(new ProgressEvent('error'));

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('Unable to load query history. Please try again.');
  });

  it('gets one conversation detail from /api/chat/history/{id}', () => {
    let result: HistoryDetail | undefined;
    service.getHistoryDetail('sess-1').subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat/history/sess-1`);
    expect(req.request.method).toBe('GET');

    const detail: HistoryDetail = { id: 'sess-1', sessionId: 'sess-1', turns: [] };
    req.flush(detail);

    expect(result).toEqual(detail);
  });

  it('falls back to a not-found message when history detail 404s without a backend message', () => {
    let caught: unknown;
    service.getHistoryDetail('no-such-id').subscribe({ error: (e) => (caught = e) });

    httpMock
      .expectOne(`${environment.apiBaseUrl}/api/chat/history/no-such-id`)
      .flush(null, { status: 404, statusText: 'Not Found' });

    expect((caught as Error).message).toBe('That conversation could not be found.');
  });

  it('deletes a conversation via DELETE /api/chat/history/{id}', () => {
    let completed = false;
    service.deleteHistory('sess-1').subscribe({ complete: () => (completed = true) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat/history/sess-1`);
    expect(req.request.method).toBe('DELETE');
    req.flush(null, { status: 204, statusText: 'No Content' });

    expect(completed).toBe(true);
  });

  it('gets one page of history and reads the total count from X-Total-Count (P1.7 rectification)', () => {
    let result: { items: HistoryItem[]; totalCount: number } | undefined;
    service.getHistoryPage(0, 2).subscribe((r) => (result = r));

    const req = httpMock.expectOne(
      (r) => r.url === `${environment.apiBaseUrl}/api/chat/history` && r.params.get('page') === '0' && r.params.get('size') === '2',
    );
    expect(req.request.method).toBe('GET');

    const mockItems: HistoryItem[] = [
      {
        id: 'sess-1',
        question: 'Is SKU-1001 in stock?',
        answerSummary: '240 units available.',
        timestamp: new Date().toISOString(),
        sessionId: 'sess-1',
      },
    ];
    req.flush(mockItems, { headers: { 'X-Total-Count': '5' } });

    expect(result?.items).toEqual(mockItems);
    expect(result?.totalCount).toBe(5);
  });
});
