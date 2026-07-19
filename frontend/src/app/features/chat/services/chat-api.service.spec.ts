import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { ChatApiService } from './chat-api.service';
import { ChatResponse } from '../models/chat.model';

describe('ChatApiService', () => {
  let service: ChatApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(ChatApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts the query and sessionId to /api/chat', () => {
    let result: ChatResponse | undefined;
    service.sendMessage('Where is order SO-45892?', 'session-1').subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ query: 'Where is order SO-45892?', sessionId: 'session-1' });

    const mockResponse: ChatResponse = {
      traceId: 't1',
      sessionId: 'session-1',
      timestamp: new Date().toISOString(),
      answerText: 'Order SO-45892 has been dispatched from the warehouse.',
      intent: 'MULTI_TOOL_QUERY',
      orderStatus: 'Dispatched',
      shipmentStatus: 'Customs Hold',
      currentLocation: 'Chennai Port',
      delayReason: 'HS code mismatch during customs validation.',
      promisedDeliveryDate: '2026-07-03',
      revisedDeliveryDate: '2026-07-09',
      delayDays: 6,
      slaStatus: 'Breached',
      recommendedActions: ['Verify the HS code in the commercial invoice.'],
      sources: [],
      partial: false,
      warnings: [],
      error: null,
      agentsInvoked: ['intent_classifier', 'text_to_sql_agent', 'api_status_agent', 'knowledge_base_agent'],
      generatedSql: null,
    };
    req.flush(mockResponse);

    expect(result).toEqual(mockResponse);
  });

  it('surfaces the backend validation message on a 400', () => {
    let caught: unknown;
    service.sendMessage('', 'session-1').subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat`);
    req.flush(
      { timestamp: new Date().toISOString(), status: 400, error: 'Bad Request', message: 'query: query must not be blank', path: '/api/chat' },
      { status: 400, statusText: 'Bad Request' },
    );

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('query: query must not be blank');
  });

  it('falls back to a generic message when the backend is unreachable', () => {
    let caught: unknown;
    service.sendMessage('Is SKU-1001 in stock?', 'session-1').subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/chat`);
    req.error(new ProgressEvent('error'));

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('Unable to retrieve the response. Please try again.');
  });
});
