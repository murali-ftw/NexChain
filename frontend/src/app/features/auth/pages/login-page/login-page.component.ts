import { Component } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-login-page',
  standalone: true,
  imports: [],
  templateUrl: './login-page.component.html',
  styleUrl: './login-page.component.scss',
})
export class LoginPageComponent {
  constructor(private readonly router: Router) {}

  onSignIn(): void {
    // Day 1: no real authentication yet — navigate straight to the chat workspace.
    this.router.navigate(['/chat']);
  }
}
