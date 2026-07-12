import { Component, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../core/services/auth.service';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [FormsModule],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.scss',
})
export class LoginPageComponent {
  email = '';
  password = '';

  readonly submitting = signal(false);
  readonly errorMessage = signal<string | null>(null);

  constructor(
    private readonly authService: AuthService,
    private readonly router: Router,
  ) {}

  onSignIn(): void {
    if (this.submitting() || !this.email.trim() || !this.password) {
      return;
    }
    this.submitting.set(true);
    this.errorMessage.set(null);

    this.authService.login(this.email.trim(), this.password).subscribe({
      next: () => {
        this.submitting.set(false);
        this.router.navigate(['/chat']);
      },
      error: (err: Error) => {
        this.submitting.set(false);
        this.errorMessage.set(err.message);
      },
    });
  }
}
