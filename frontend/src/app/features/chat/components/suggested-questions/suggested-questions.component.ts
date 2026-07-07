import { Component, EventEmitter, Output } from '@angular/core';

interface SuggestedQuestionGroup {
  category: string;
  questions: string[];
}

@Component({
  selector: 'app-suggested-questions',
  standalone: true,
  imports: [],
  templateUrl: './suggested-questions.component.html',
  styleUrl: './suggested-questions.component.scss',
})
export class SuggestedQuestionsComponent {
  @Output() questionSelected = new EventEmitter<string>();

  readonly groups: SuggestedQuestionGroup[] = [
    {
      category: 'Order & Shipment Status',
      questions: ['Where is order SO-45892?', 'Why is order SO-45892 delayed?'],
    },
    {
      category: 'Inventory Availability',
      questions: ['Is SKU-1001 in stock?'],
    },
    {
      category: 'SLA & Delay Policy',
      questions: ['What is the SLA breach escalation process?'],
    },
    {
      category: 'Reporting',
      questions: ['Show delayed orders from Chennai warehouse.'],
    },
  ];

  select(question: string): void {
    this.questionSelected.emit(question);
  }
}
