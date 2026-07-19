import { inject } from '@angular/core';
import { CanActivateFn, Router } from '@angular/router';
import { AuthService } from '../services/auth.service';

/** Day 12 hardening: /audit is ADMIN-only server-side (Spring Security's
 * `hasRole("ADMIN")` on `/api/audit/**`) but had no client-side guard, so a
 * non-admin navigating there directly saw the page attempt to load and fail
 * with repeated 403s instead of being kept out. authGuard already ran first
 * (route nesting), so a non-admin here is authenticated but unauthorized —
 * redirect to /chat rather than /login. */
export const adminGuard: CanActivateFn = () => {
  const authService = inject(AuthService);
  const router = inject(Router);

  return authService.currentUser()?.role === 'ADMIN' ? true : router.createUrlTree(['/chat']);
};
