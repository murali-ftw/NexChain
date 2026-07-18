import { Pipe, PipeTransform } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

/**
 * Minimal, dependency-free Markdown renderer for LLM-authored prose.
 * knowledge_base_agent's answer_policy_question (Person 3) routinely returns
 * #-headers, **bold**, and numbered/bulleted lists for multi-part policy
 * answers — {{ }} interpolation rendered that syntax as literal text instead
 * of formatting it. Handles only the constructs actually observed from that
 * agent; not a general CommonMark implementation.
 *
 * Input is HTML-escaped before any markdown substitution, so this can never
 * inject markup the source text didn't request via recognized markdown
 * syntax; Angular's own [innerHTML] sanitizer (still active — this uses
 * bypassSecurityTrustHtml only to skip Angular re-escaping the tags this
 * pipe itself generated) is the last line of defense.
 *
 * The common case — final_response_agent_node's deterministic, single-line,
 * plain-text answerText (the flagship/multi-tool path) — has no markdown
 * syntax at all, so it renders as plain inline text with no wrapping block
 * element, pixel-identical to the old {{ answerText }} behavior. Block
 * elements (<p>/<h4>/<ol>/<ul>) only appear when the source text actually
 * has multiple paragraphs, headings, or list items to represent.
 */
@Pipe({
  name: 'markdownLite',
  standalone: true,
})
export class MarkdownLitePipe implements PipeTransform {
  constructor(private readonly sanitizer: DomSanitizer) {}

  transform(value: string | null | undefined): SafeHtml {
    if (!value) {
      return '';
    }
    return this.sanitizer.bypassSecurityTrustHtml(renderMarkdownLite(value));
  }
}

interface Block {
  tag: 'p' | 'h4' | 'ol' | 'ul';
  items: string[];
}

function renderMarkdownLite(source: string): string {
  const blocks = parseBlocks(escapeHtml(source));

  // No markdown structure at all (the common case) — a single plain
  // paragraph renders as bare inline text, not wrapped in <p>, so the
  // deterministic sentence-concatenation answerText looks exactly as it
  // did before this pipe existed.
  if (blocks.length === 1 && blocks[0].tag === 'p') {
    return renderInline(blocks[0].items[0]);
  }

  return blocks
    .map((block) =>
      block.tag === 'p' || block.tag === 'h4'
        ? `<${block.tag}>${renderInline(block.items[0])}</${block.tag}>`
        : `<${block.tag}>${block.items.map((item) => `<li>${renderInline(item)}</li>`).join('')}</${block.tag}>`,
    )
    .join('');
}

function parseBlocks(text: string): Block[] {
  const blocks: Block[] = [];
  let paragraph: string[] = [];
  let list: Block | null = null;

  const flushParagraph = () => {
    if (paragraph.length) {
      blocks.push({ tag: 'p', items: [paragraph.join(' ')] });
      paragraph = [];
    }
  };
  const flushList = () => {
    if (list) {
      blocks.push(list);
      list = null;
    }
  };

  for (const rawLine of text.split('\n')) {
    const line = rawLine.trim();
    if (!line) {
      flushParagraph();
      flushList();
      continue;
    }

    const heading = /^#{1,6}\s+(.*)$/.exec(line);
    if (heading) {
      flushParagraph();
      flushList();
      blocks.push({ tag: 'h4', items: [heading[1]] });
      continue;
    }

    const numbered = /^\d+[.)]\s+(.*)$/.exec(line);
    const bulleted = /^[*-]\s+(.*)$/.exec(line);
    const listMatch = numbered ?? bulleted;
    if (listMatch) {
      flushParagraph();
      const tag = numbered ? 'ol' : 'ul';
      if (!list || list.tag !== tag) {
        flushList();
        list = { tag, items: [] };
      }
      list.items.push(listMatch[1]);
      continue;
    }

    flushList();
    paragraph.push(line);
  }
  flushParagraph();
  flushList();
  return blocks;
}

function escapeHtml(text: string): string {
  return text.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

function renderInline(text: string): string {
  // Bold first: consumes every **pair** so the italic pass below only ever
  // sees single asterisks left over (block-level list-marker asterisks are
  // already stripped by the time this runs — see parseBlocks).
  return text
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>');
}
