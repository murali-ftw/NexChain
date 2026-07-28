import { HttpErrorResponse, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { catchError, throwError } from 'rxjs';
import { AuthService } from '../services/auth.service';
import { LoggerService } from '../services/logger.service';

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
  const logger = inject(LoggerService);
  const token = authService.getToken();

  const authorizedReq = token ? req.clone({ setHeaders: { Authorization: `Bearer ${token}` } }) : req;

  return next(authorizedReq).pipe(
    catchError((err: HttpErrorResponse) => {
      if (err.status === 401 && authService.isAuthenticated()) {
        // Never log the token itself — just the outcome and which path triggered it.
        logger.warn('auth session invalidated by 401, logging out', { path: req.url });
        authService.logout();
      }
      return throwError(() => err);
    }),
  );
};
