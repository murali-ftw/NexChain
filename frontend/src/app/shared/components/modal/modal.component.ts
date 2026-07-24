import {
  AfterViewInit,
  Component,
  ElementRef,
  EventEmitter,
  Input,
  OnChanges,
  Output,
  SimpleChanges,
  ViewChild,
} from '@angular/core';

/**
 * Wraps the native <dialog> element rather than a hand-rolled overlay:
 * showModal()/close() give focus-trapping, ESC-to-close, and a top-layer
 * backdrop for free.
 */
@Component({
  selector: 'app-modal',
  standalone: true,
  imports: [],
  templateUrl: './modal.component.html',
  styleUrl: './modal.component.scss',
})
export class ModalComponent implements OnChanges, AfterViewInit {
  @Input() open = false;
  @Input() titleText = '';
  @Output() closed = new EventEmitter<void>();

  @ViewChild('dialogEl') private readonly dialogElRef!: ElementRef<HTMLDialogElement>;

  ngAfterViewInit(): void {
    if (this.open) {
      this.dialogElRef.nativeElement.showModal();
    }
  }

  ngOnChanges(changes: SimpleChanges): void {
    if (!('open' in changes) || !this.dialogElRef) {
      return;
    }
    const dialog = this.dialogElRef.nativeElement;
    if (this.open && !dialog.open) {
      dialog.showModal();
    } else if (!this.open && dialog.open) {
      dialog.close();
    }
  }

  close(): void {
    this.dialogElRef.nativeElement.close();
  }

  onDialogClose(): void {
    this.closed.emit();
  }

  onBackdropClick(event: MouseEvent): void {
    if (event.target === this.dialogElRef.nativeElement) {
      this.close();
    }
  }
}
