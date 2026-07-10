import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { HistoryApiService } from './history-api.service';
import { HistoryItem } from '../models/history.model';

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
});
