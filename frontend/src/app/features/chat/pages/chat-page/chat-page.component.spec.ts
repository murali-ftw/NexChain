import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { environment } from '../../../../../environments/environment';
import {
  FLAGSHIP_RESPONSE,
  INVENTORY_RESPONSE,
  REPORTING_RESPONSE,
  SLA_POLICY_RESPONSE,
} from '../../data/chat-fixtures';
import { ChatResponse } from '../../models/chat.model';
import { ChatPageComponent } from './chat-page.component';

const CHAT_URL = `${environment.apiBaseUrl}/api/chat`;

/** Builds a full ChatResponse from a Day 3 fixture, as Spring Boot would return it. */
function toWireResponse(fixture: Omit<ChatResponse, 'traceId' | 'sessionId' | 'timestamp'>): ChatResponse {
  return { ...fixture, traceId: 'trace-1', sessionId: 'session-1', timestamp: new Date().toISOString() };
}

describe('ChatPageComponent', () => {
  let httpMock: HttpTestingController;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatPageComponent],
      providers: [provideHttpClient(), provideHttpClientTesting()],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('renders the empty state and suggested questions in the DOM', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Ask a supply chain question');
    expect(text).toContain('Where is order SO-45892?');
  });

  it('rejects blank and whitespace-only input', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('');
    component.onSend('   ');

    expect(component.messages().length).toBe(0);
    httpMock.expectNone(CHAT_URL);
  });

  it('sends a real HTTP request and renders the flagship response from it — not a local mock', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const el = fixture.nativeElement as HTMLElement;

    component.onSend('Where is order SO-45892? Why is it delayed and what action should we take?');
    fixture.detectChanges();

    // User message appears immediately, loading state is active — both in state and DOM.
    expect(component.messages().length).toBe(1);
    expect(component.messages()[0].kind).toBe('user');
    expect(component.isLoading()).toBe(true);
    expect(el.textContent).toContain('Where is order SO-45892?');
    expect(el.textContent).toContain('Checking order and shipment status...');

    const req = httpMock.expectOne(CHAT_URL);
    expect(req.request.method).toBe('POST');
    expect(req.request.body.query).toBe('Where is order SO-45892? Why is it delayed and what action should we take?');

    // Nothing resolves until Spring Boot actually answers — proves there is no
    // remaining local success-mock shortcut for the primary flow.
    expect(component.messages().length).toBe(1);

    req.flush(toWireResponse(FLAGSHIP_RESPONSE));
    fixture.detectChanges();

    expect(component.isLoading()).toBe(false);
    expect(component.messages().length).toBe(2);
    const assistantMessage = component.messages()[1];
    expect(assistantMessage.kind).toBe('assistant');
    if (assistantMessage.kind === 'assistant') {
      expect(assistantMessage.response.slaStatus).toBe('Breached');
      expect(assistantMessage.response.delayDays).toBe(6);
    }

    // Rendered structured sections: headline, impact, recommended actions, sources.
    expect(el.textContent).toContain('Order SO-45892 has been dispatched from the warehouse.');
    expect(el.textContent).toContain('Customs Hold');
    expect(el.textContent).toContain('2026-07-03');
    expect(el.textContent).toContain('2026-07-09');
    expect(el.textContent).toContain('6 days');
    expect(el.textContent).toContain('Breached');
    expect(el.textContent).toContain('Verify the HS code in the commercial invoice.');
    expect(el.textContent).toContain('Customs Hold SOP');
    expect(el.querySelectorAll('.source-badge').length).toBeGreaterThan(0);
    expect(el.textContent).not.toContain('Checking order and shipment status...');
  });

  it('ignores a second send while a request is already in flight (only one HTTP call made)', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('Is SKU-1001 in stock?');
    component.onSend('Show delayed orders from Chennai warehouse.');

    // Only the first user message was accepted while loading, and httpMock.expectOne
    // below would fail if a second request had been fired.
    expect(component.messages().length).toBe(1);

    const req = httpMock.expectOne(CHAT_URL);
    req.flush(toWireResponse(INVENTORY_RESPONSE));

    expect(component.messages().length).toBe(2);
  });

  it('keeps chronological order across multiple HTTP-backed turns', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('Is SKU-1001 in stock?');
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(INVENTORY_RESPONSE));
    fixture.detectChanges();

    component.onSend('What is the SLA breach escalation process?');
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(SLA_POLICY_RESPONSE));
    fixture.detectChanges();

    component.onSend('Show delayed orders from Chennai warehouse.');
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(REPORTING_RESPONSE));
    fixture.detectChanges();

    const kinds = component.messages().map((m) => m.kind);
    expect(kinds).toEqual(['user', 'assistant', 'user', 'assistant', 'user', 'assistant']);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Is SKU-1001 in stock?');
    expect(text).toContain('What is the SLA breach escalation process?');
    expect(text).toContain('Show delayed orders from Chennai warehouse.');
  });

  it('shows the frontend error state when the backend returns a 5xx', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;
    const el = fixture.nativeElement as HTMLElement;

    component.onSend('Is SKU-1001 in stock?');
    const req = httpMock.expectOne(CHAT_URL);
    req.flush('Internal error', { status: 500, statusText: 'Internal Server Error' });
    fixture.detectChanges();

    expect(component.isLoading()).toBe(false);
    expect(component.messages()[1].kind).toBe('error');
    expect(el.textContent).toContain('Unable to retrieve the response. Please try again.');
    expect(el.querySelector('.chat-error__retry')).toBeTruthy();

    // Page must still be usable — another message can be sent.
    component.onSend('Show delayed orders from Chennai warehouse.');
    expect(component.isLoading()).toBe(true);
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(REPORTING_RESPONSE));

    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('assistant');
  });

  it('retry() re-sends the original failed query as a fresh HTTP request', () => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('Is SKU-1001 in stock?');
    httpMock.expectOne(CHAT_URL).flush('error', { status: 500, statusText: 'Internal Server Error' });
    const errorMessage = component.messages()[1];
    expect(errorMessage.kind).toBe('error');

    if (errorMessage.kind === 'error') {
      component.retry(errorMessage.retryText);
    }
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(INVENTORY_RESPONSE));

    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('assistant');
  });

  it('renders a degraded response with a visible warning via the local test trigger (no HTTP call)', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate degraded');
    tick(600);
    fixture.detectChanges();
    httpMock.expectNone(CHAT_URL);

    const message = component.messages()[1];
    expect(message.kind).toBe('assistant');
    if (message.kind === 'assistant') {
      expect(message.response.partial).toBe(true);
      expect(message.response.warnings.length).toBeGreaterThan(0);
    }

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Shipment API unavailable. This answer is based on database records only.');
  }));

  it('shows an error message via the local test trigger and allows sending another message afterward', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate error');
    tick(600);
    fixture.detectChanges();
    httpMock.expectNone(CHAT_URL);

    expect(component.messages()[1].kind).toBe('error');
    expect(component.isLoading()).toBe(false);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Unable to retrieve the response. Please try again.');

    // Page must still be usable — another message can be sent, this time for real.
    component.onSend('Is SKU-1001 in stock?');
    expect(component.isLoading()).toBe(true);
    httpMock.expectOne(CHAT_URL).flush(toWireResponse(INVENTORY_RESPONSE));

    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('assistant');
  }));

  it('retry() re-sends "simulate error" and deterministically errors again', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate error');
    tick(600);
    const errorMessage = component.messages()[1];
    expect(errorMessage.kind).toBe('error');

    if (errorMessage.kind === 'error') {
      component.retry(errorMessage.retryText);
    }
    tick(600);
    fixture.detectChanges();

    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('error');
  }));
});
