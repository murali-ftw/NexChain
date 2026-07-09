import { TestBed } from '@angular/core/testing';
import { ChatInputComponent } from './chat-input.component';

describe('ChatInputComponent', () => {
  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ChatInputComponent],
    }).compileComponents();
  });

  it('does not emit for a blank message', () => {
    const fixture = TestBed.createComponent(ChatInputComponent);
    const component = fixture.componentInstance;
    const emitted: string[] = [];
    component.send.subscribe((text) => emitted.push(text));

    component.message = '';
    component.submit();
    component.message = '   ';
    component.submit();

    expect(emitted.length).toBe(0);
  });

  it('emits the trimmed message and clears the input on submit', () => {
    const fixture = TestBed.createComponent(ChatInputComponent);
    const component = fixture.componentInstance;
    const emitted: string[] = [];
    component.send.subscribe((text) => emitted.push(text));

    component.message = '  Where is order SO-45892?  ';
    component.submit();

    expect(emitted).toEqual(['Where is order SO-45892?']);
    expect(component.message).toBe('');
  });

  it('does not submit while disabled', () => {
    const fixture = TestBed.createComponent(ChatInputComponent);
    const component = fixture.componentInstance;
    const emitted: string[] = [];
    component.send.subscribe((text) => emitted.push(text));

    component.disabled = true;
    component.message = 'Is SKU-1001 in stock?';
    component.submit();

    expect(emitted.length).toBe(0);
  });

  it('Shift+Enter does not submit; plain Enter does', () => {
    const fixture = TestBed.createComponent(ChatInputComponent);
    const component = fixture.componentInstance;
    const emitted: string[] = [];
    component.send.subscribe((text) => emitted.push(text));

    component.message = 'line one';
    component.onEnter({ shiftKey: true, preventDefault: () => {} } as unknown as Event);
    expect(emitted.length).toBe(0);
    expect(component.message).toBe('line one');

    component.onEnter({ shiftKey: false, preventDefault: () => {} } as unknown as Event);
    expect(emitted).toEqual(['line one']);
  });
});
