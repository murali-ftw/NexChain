import { provideHttpClient } from '@angular/common/http';
import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { HistoryItem } from '../../models/history.model';
import { HistoryPageComponent } from './history-page.component';

const HISTORY_URL = `${environment.apiBaseUrl}/api/chat/history`;

const ITEMS: HistoryItem[] = [
  {
    id: 'sess-1',
    question: 'Is SKU-1001 in stock?',
    answerSummary: '240 units available at the Chennai warehouse.',
    timestamp: new Date().toISOString(),
    sessionId: 'sess-1',
  },
  {
    id: 'sess-2',
    question: 'What is the SLA breach escalation process?',
    answerSummary: 'SLA breaches are escalated based on the customer tier.',
    timestamp: new Date().toISOString(),
    sessionId: 'sess-2',
  },
];

describe('HistoryPageComponent', () => {
  let httpMock: HttpTestingController;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(async () => {
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    await TestBed.configureTestingModule({
      imports: [HistoryPageComponent],
      providers: [provideHttpClient(), provideHttpClientTesting(), { provide: Router, useValue: routerSpy }],
    }).compileComponents();
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('shows the empty state when there is no history yet', () => {
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();

    httpMock.expectOne(HISTORY_URL).flush([]);
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain("You haven't asked anything yet.");
  });

  it('renders every loaded conversation', () => {
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();

    httpMock.expectOne(HISTORY_URL).flush(ITEMS);
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).toContain('Is SKU-1001 in stock?');
    expect(text).toContain('What is the SLA breach escalation process?');
  });

  it('search filters the list to matching conversations', () => {
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(HISTORY_URL).flush(ITEMS);
    fixture.detectChanges();

    const component = fixture.componentInstance;
    component.onSearchTermChange('SLA');
    fixture.detectChanges();

    const text = (fixture.nativeElement as HTMLElement).textContent ?? '';
    expect(text).not.toContain('Is SKU-1001 in stock?');
    expect(text).toContain('What is the SLA breach escalation process?');
  });

  it('restore navigates to /chat with the conversation session id', () => {
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(HISTORY_URL).flush(ITEMS);
    fixture.detectChanges();

    fixture.componentInstance.restore(ITEMS[0]);

    expect(routerSpy.navigate).toHaveBeenCalledWith(['/chat'], { queryParams: { sessionId: 'sess-1' } });
  });

  it('delete removes the conversation from the list on success after confirmation', () => {
    spyOn(window, 'confirm').and.returnValue(true);
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(HISTORY_URL).flush(ITEMS);
    fixture.detectChanges();

    fixture.componentInstance.confirmRemove(ITEMS[0]);
    httpMock.expectOne(`${HISTORY_URL}/sess-1`).flush(null, { status: 204, statusText: 'No Content' });
    fixture.detectChanges();

    expect(fixture.componentInstance.items().length).toBe(1);
    expect((fixture.nativeElement as HTMLElement).textContent).not.toContain('Is SKU-1001 in stock?');
  });

  it('delete does nothing when the user cancels the confirmation', () => {
    spyOn(window, 'confirm').and.returnValue(false);
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();
    httpMock.expectOne(HISTORY_URL).flush(ITEMS);
    fixture.detectChanges();

    fixture.componentInstance.confirmRemove(ITEMS[0]);

    expect(fixture.componentInstance.items().length).toBe(2);
  });

  it('shows an error message when the history request fails', () => {
    const fixture = TestBed.createComponent(HistoryPageComponent);
    fixture.detectChanges();

    httpMock.expectOne(HISTORY_URL).error(new ProgressEvent('error'));
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).textContent).toContain(
      'Unable to load query history. Please try again.',
    );
  });
});
