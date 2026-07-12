import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';

/**
 * Day 6 (P1.6): attaches `Authorization: Bearer <token>` to every outgoing
 * request when a session exists. Also handles the inverse of login — if the
 * backend ever rejects a token as invalid/expired (401), the session is no
 * longer valid client-side either, so it clears state and redirects to
 * /login the same way an explicit logout does, rather than leaving the UI
 * stuck showing protected content behind failed requests.
 */
export const authInterceptor: HttpInterceptorFn = (req, next) => {
  const authService = inject(AuthService);
  const token = authService.getToken();

  const authorizedReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authorizedReq).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401 && authService.isAuthenticated()) {
        authService.logout();
      }
      return throwError(() => err);
    }),
  );
};
