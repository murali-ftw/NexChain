import { SecurityContext } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { DomSanitizer } from '@angular/platform-browser';
import { MarkdownLitePipe } from './markdown-lite.pipe';

describe('MarkdownLitePipe', () => {
  let pipe: MarkdownLitePipe;
  let sanitizer: DomSanitizer;

  beforeEach(() => {
    sanitizer = TestBed.inject(DomSanitizer);
    pipe = new MarkdownLitePipe(sanitizer);
  });

  function render(value: string | null | undefined): string {
    return sanitizer.sanitize(SecurityContext.HTML, pipe.transform(value)) ?? '';
  }

  it('returns an empty string for null/undefined/empty input', () => {
    expect(render(null)).toBe('');
    expect(render(undefined)).toBe('');
    expect(render('')).toBe('');
  });

  it('renders a single plain sentence with no wrapping block element (the deterministic flagship-path case)', () => {
    const text = 'Order SO-45892 is currently Delayed. SLA status: Breached (6 day(s) past the promised date).';
    expect(render(text)).toBe(text);
  });

  it('renders **bold** inline without a wrapping block for single-line input', () => {
    expect(render('Escalate to the **Logistics Manager** immediately.')).toBe(
      'Escalate to the <strong>Logistics Manager</strong> immediately.',
    );
  });

  it('renders single-asterisk *italic* without conflicting with **bold**', () => {
    expect(render('*Trigger:* Order is **Breached**.')).toBe(
      '<em>Trigger:</em> Order is <strong>Breached</strong>.',
    );
  });

  it('renders a # heading as h4', () => {
    expect(render('### Escalation Roles by SLA Tier')).toBe('<h4>Escalation Roles by SLA Tier</h4>');
  });

  it('renders a numbered list as ol/li', () => {
    const text = ['1. Verify the HS code.', '2. Notify the customer.'].join('\n');
    expect(render(text)).toBe('<ol><li>Verify the HS code.</li><li>Notify the customer.</li></ol>');
  });

  it('renders a bulleted list as ul/li', () => {
    const text = ['* STANDARD tier: 3 days.', '* GOLD tier: 5 days.'].join('\n');
    expect(render(text)).toBe('<ul><li>STANDARD tier: 3 days.</li><li>GOLD tier: 5 days.</li></ul>');
  });

  it('renders multiple paragraphs as separate <p> elements', () => {
    const text = ['First paragraph.', '', 'Second paragraph.'].join('\n');
    expect(render(text)).toBe('<p>First paragraph.</p><p>Second paragraph.</p>');
  });

  it('HTML-escapes the source before applying markdown, so it cannot inject arbitrary markup', () => {
    const text = 'Contains a <script>alert(1)</script> tag and a <img src=x onerror=alert(1)> tag.';
    const rendered = render(text);
    expect(rendered).not.toContain('<script>');
    expect(rendered).not.toContain('<img');
    expect(rendered).toContain('&lt;script&gt;');
  });

  it('renders a realistic multi-section policy answer with headings, bold, and lists together', () => {
    const text = [
      'Based on the provided policy context:',
      '',
      '### 1. Escalation Roles by SLA Tier',
      '* **STANDARD Tier**: Escalates to Logistics Coordinator.',
      '* **GOLD Tier**: Escalates to Logistics Manager.',
    ].join('\n');
    const rendered = render(text);
    expect(rendered).toContain('<h4>1. Escalation Roles by SLA Tier</h4>');
    expect(rendered).toContain('<strong>STANDARD Tier</strong>');
    expect(rendered).toContain('<ul><li>');
  });
});
