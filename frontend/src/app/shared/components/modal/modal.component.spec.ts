import { TestBed } from '@angular/core/testing';
import { ModalComponent } from './modal.component';

describe('ModalComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ModalComponent],
    }).compileComponents();
  });

  it('opens the native dialog when `open` becomes true and emits `closed` when it closes', (done) => {
    const fixture = TestBed.createComponent(ModalComponent);
    fixture.detectChanges();
    const dialog: HTMLDialogElement = fixture.nativeElement.querySelector('dialog');
    expect(dialog.open).toBeFalse();

    fixture.componentInstance.open = true;
    fixture.componentInstance.ngOnChanges({
      open: { currentValue: true, previousValue: false, firstChange: false, isFirstChange: () => false },
    });
    expect(dialog.open).toBeTrue();

    // dialog.close() queues its 'close' event as a browser task rather than
    // firing it synchronously (HTML spec), so this has to be asserted async.
    fixture.componentInstance.closed.subscribe(() => {
      expect(dialog.open).toBeFalse();
      done();
    });
    fixture.componentInstance.close();
  });
});
