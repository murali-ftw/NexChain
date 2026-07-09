import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ChatMockService } from './chat-mock.service';

describe('ChatMockService', () => {
  let service: ChatMockService;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    service = TestBed.inject(ChatMockService);
  });

  it('resolves the flagship scenario for a query mentioning SO-45892', fakeAsync(() => {
    let result: any;
    service.getResponse('Where is order SO-45892?', 'session-1').subscribe((r) => (result = r));
    tick(1000);

    expect(result.slaStatus).toBe('Breached');
    expect(result.delayDays).toBe(6);
    expect(result.promisedDeliveryDate).toBe('2026-07-03');
    expect(result.revisedDeliveryDate).toBe('2026-07-09');
    expect(result.recommendedActions.length).toBe(4);
    expect(result.intent).toBe('MULTI_TOOL_QUERY');
    expect(result.sessionId).toBe('session-1');
    expect(result.traceId).toBeTruthy();
  }));

  it('resolves the inventory scenario for a stock question', fakeAsync(() => {
    let result: any;
    service.getResponse('Is SKU-1001 in stock?', 's').subscribe((r) => (result = r));
    tick(1000);

    expect(result.intent).toBe('DATABASE_QUERY');
    expect(result.slaStatus).toBe('N/A');
    expect(result.answerText).toContain('SKU-1001');
  }));

  it('resolves the SLA/SOP scenario for an escalation question', fakeAsync(() => {
    let result: any;
    service.getResponse('What is the SLA breach escalation process?', 's').subscribe((r) => (result = r));
    tick(1000);

    expect(result.intent).toBe('KNOWLEDGE_QUERY');
    expect(result.sources.length).toBeGreaterThan(0);
  }));

  it('resolves the reporting scenario for a warehouse report question', fakeAsync(() => {
    let result: any;
    service.getResponse('Show delayed orders from Chennai warehouse.', 's').subscribe((r) => (result = r));
    tick(1000);

    expect(result.intent).toBe('DATABASE_QUERY');
    expect(result.answerText).toContain('Chennai warehouse');
  }));

  it('resolves the degraded scenario on the "simulate degraded" trigger', fakeAsync(() => {
    let result: any;
    service.getResponse('simulate degraded', 's').subscribe((r) => (result = r));
    tick(1000);

    expect(result.partial).toBe(true);
    expect(result.warnings.length).toBeGreaterThan(0);
  }));

  it('errors on the "simulate error" trigger', fakeAsync(() => {
    let caught: unknown;
    service.getResponse('simulate error', 's').subscribe({ error: (e) => (caught = e) });
    tick(1000);

    expect(caught).toBeTruthy();
    expect((caught as Error).message).toContain('Unable to retrieve the response');
  }));

  it('falls back to a generic mock for an unrecognized query', fakeAsync(() => {
    let result: any;
    service.getResponse('what time is it', 's').subscribe((r) => (result = r));
    tick(1000);

    expect(result.answerText).toContain('what time is it');
    expect(result.slaStatus).toBe('N/A');
  }));
});
