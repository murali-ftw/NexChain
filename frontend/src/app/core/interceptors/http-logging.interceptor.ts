import { HttpErrorResponse, HttpEventType, HttpInterceptorFn } from '@angular/common/http';
import { inject } from '@angular/core';
import { tap } from 'rxjs/operators';
import { LoggerService } from '../services/logger.service';

/**
 * Client-side counterpart to the request/response summary line every backend
 * service logs (RequestCorrelationFilter in backend-api, RequestContextMiddleware
 * in the Python services) — method, path, status, duration. DEBUG-level, so
 * it's silent by default in production (environment.ts's logLevel) and only
 * surfaces when a developer opts into DEBUG locally — no request/response
 * bodies are logged, only the safe metadata already visible in DevTools' own
 * Network tab.
 */
export const httpLoggingInterceptor: HttpInterceptorFn = (req, next) => {
  const logger = inject(LoggerService);
  const startedAt = performance.now();

  return next(req).pipe(
    tap({
      next: (event) => {
        if (event.type === HttpEventType.Response) {
          const durationMs = Math.round(performance.now() - startedAt);
          const requestId = event.headers.get('X-Request-ID');
          logger.debug(`http ${req.method} ${req.urlWithParams} -> ${event.status}`, {
            durationMs,
            requestId,
          });
        }
      },
      error: (err: HttpErrorResponse) => {
        const durationMs = Math.round(performance.now() - startedAt);
        const requestId = err.headers?.get('X-Request-ID') ?? null;
        logger.warn(`http ${req.method} ${req.urlWithParams} -> ${err.status}`, {
          durationMs,
          requestId,
        });
      },
    }),
  );
};
