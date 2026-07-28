import { inject, Injectable, InjectionToken } from '@angular/core';
import { environment } from '../../../environments/environment';

export type LogLevel = 'debug' | 'info' | 'warn' | 'error';

const LEVEL_ORDER: Record<LogLevel, number> = { debug: 0, info: 1, warn: 2, error: 3 };

/**
 * Defaults to the current build's environment.ts, but is a real DI token
 * (not a direct import inside LoggerService) so tests can override it to
 * assert filtering behavior deterministically instead of depending on
 * whichever environment file happens to be file-replaced into the test build.
 */
export const LOG_LEVEL = new InjectionToken<LogLevel>('LOG_LEVEL', {
  providedIn: 'root',
  factory: () => environment.logLevel,
});

/**
 * Thin wrapper around `console.*` so log level is environment-controlled
 * (see environment.ts/environment.development.ts's `logLevel`) instead of
 * every call site deciding for itself whether to print. Mirrors the backend
 * services' own default-levels convention: INFO for normal activity, WARN
 * for recoverable/unexpected conditions, ERROR for failures, DEBUG for
 * diagnostic detail that's off by default in production.
 *
 * Never pass a JWT, password, or full request/response body to this service
 * — same rule the backend follows (see README.md "Logging"). Log safe
 * identifiers (a request id, a route path, a status code), not raw payloads.
 */
@Injectable({ providedIn: 'root' })
export class LoggerService {
  private readonly minLevel: LogLevel = inject(LOG_LEVEL);

  debug(message: string, ...args: unknown[]): void {
    this.write('debug', message, args);
  }

  info(message: string, ...args: unknown[]): void {
    this.write('info', message, args);
  }

  warn(message: string, ...args: unknown[]): void {
    this.write('warn', message, args);
  }

  error(message: string, ...args: unknown[]): void {
    this.write('error', message, args);
  }

  private write(level: LogLevel, message: string, args: unknown[]): void {
    if (LEVEL_ORDER[level] < LEVEL_ORDER[this.minLevel]) {
      return;
    }
    const consoleMethod = level === 'debug' ? 'log' : level;
    // eslint-disable-next-line no-console -- this is the one sanctioned console call site
    console[consoleMethod](`[${level.toUpperCase()}] ${message}`, ...args);
  }
}
