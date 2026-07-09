import { fakeAsync, TestBed, tick } from '@angular/core/testing';
import { ChatPageComponent } from './chat-page.component';

describe('ChatPageComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatPageComponent],
    }).compileComponents();
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
  });

  it('runs the full send -> loading -> response flow and renders it in the DOM', fakeAsync(() => {
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

    tick(1000);
    fixture.detectChanges();

    // Loading clears, assistant message appended and fully rendered.
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
  }));

  it('ignores a second send while a request is already in flight', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('Is SKU-1001 in stock?');
    component.onSend('Show delayed orders from Chennai warehouse.');

    // Only the first user message was accepted while loading.
    expect(component.messages().length).toBe(1);

    tick(1000);
    expect(component.messages().length).toBe(2);
  }));

  it('keeps chronological order across multiple turns', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('Is SKU-1001 in stock?');
    tick(1000);
    fixture.detectChanges();
    component.onSend('What is the SLA breach escalation process?');
    tick(1000);
    fixture.detectChanges();
    component.onSend('Show delayed orders from Chennai warehouse.');
    tick(1000);
    fixture.detectChanges();

    const kinds = component.messages().map((m) => m.kind);
    expect(kinds).toEqual(['user', 'assistant', 'user', 'assistant', 'user', 'assistant']);

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Is SKU-1001 in stock?');
    expect(text).toContain('What is the SLA breach escalation process?');
    expect(text).toContain('Show delayed orders from Chennai warehouse.');
  }));

  it('renders a degraded response with a visible warning instead of a hard error', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate degraded');
    tick(1000);
    fixture.detectChanges();

    const message = component.messages()[1];
    expect(message.kind).toBe('assistant');
    if (message.kind === 'assistant') {
      expect(message.response.partial).toBe(true);
      expect(message.response.warnings.length).toBeGreaterThan(0);
    }

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Shipment API unavailable. This answer is based on database records only.');
  }));

  it('shows an error message in the DOM and allows sending another message afterward', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate error');
    tick(1000);
    fixture.detectChanges();

    expect(component.messages()[1].kind).toBe('error');
    expect(component.isLoading()).toBe(false);
    const el = fixture.nativeElement as HTMLElement;
    expect(el.textContent).toContain('Unable to retrieve the response. Please try again.');
    expect(el.querySelector('.chat-error__retry')).toBeTruthy();

    // Page must still be usable — another message can be sent.
    component.onSend('Is SKU-1001 in stock?');
    expect(component.isLoading()).toBe(true);
    tick(1000);
    fixture.detectChanges();

    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('assistant');
  }));

  it('retry() re-sends the original failed query', fakeAsync(() => {
    const fixture = TestBed.createComponent(ChatPageComponent);
    fixture.detectChanges();
    const component = fixture.componentInstance;

    component.onSend('simulate error');
    tick(1000);
    const errorMessage = component.messages()[1];
    expect(errorMessage.kind).toBe('error');

    if (errorMessage.kind === 'error') {
      component.retry(errorMessage.retryText);
    }
    tick(1000);
    fixture.detectChanges();

    // Retrying "simulate error" deterministically errors again — proves retry re-invokes onSend.
    expect(component.messages().length).toBe(4);
    expect(component.messages()[3].kind).toBe('error');
  }));
});
