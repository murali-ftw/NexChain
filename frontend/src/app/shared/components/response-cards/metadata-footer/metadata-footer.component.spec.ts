import { TestBed } from '@angular/core/testing';
import { MetadataFooterComponent } from './metadata-footer.component';

describe('MetadataFooterComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [MetadataFooterComponent],
    }).compileComponents();
  });

  function create(): { fixture: ReturnType<typeof TestBed.createComponent<MetadataFooterComponent>> } {
    const fixture = TestBed.createComponent(MetadataFooterComponent);
    fixture.componentInstance.traceId = 'trace-123';
    fixture.componentInstance.timestamp = '2026-07-19T00:00:00Z';
    return { fixture };
  }

  it('renders no error banner when error is null (the common case)', () => {
    const { fixture } = create();
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.error')).toBeNull();
  });

  it('renders the error banner when the response carries a structured error', () => {
    const { fixture } = create();
    fixture.componentInstance.error = 'cannot reach the database: connection refused';
    fixture.detectChanges();

    const banner = fixture.nativeElement.querySelector('.error[role="alert"]');
    expect(banner).not.toBeNull();
    expect(banner.textContent).toContain('cannot reach the database: connection refused');
  });

  it('renders both the error banner and warnings when both are present', () => {
    const { fixture } = create();
    fixture.componentInstance.error = 'partial failure';
    fixture.componentInstance.warnings = ['SLA data may be stale'];
    fixture.detectChanges();

    expect(fixture.nativeElement.querySelector('.error')).not.toBeNull();
    expect(fixture.nativeElement.querySelector('.warnings')).not.toBeNull();
  });
});
