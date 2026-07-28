import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { httpLoggingInterceptor } from './http-logging.interceptor';
import { LoggerService } from '../services/logger.service';

describe('httpLoggingInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let loggerSpy: jasmine.SpyObj<LoggerService>;

  beforeEach(() => {
    loggerSpy = jasmine.createSpyObj('LoggerService', ['debug', 'warn']);

    TestBed.configureTestingModule({
      providers: [
        { provide: LoggerService, useValue: loggerSpy },
        provideHttpClient(withInterceptors([httpLoggingInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('logs a successful response at debug with method, status, and duration', () => {
    http.get('/api/health').subscribe();

    const req = httpMock.expectOne('/api/health');
    req.flush({ status: 'UP' }, { status: 200, statusText: 'OK' });

    expect(loggerSpy.debug).toHaveBeenCalledTimes(1);
    const [message, meta] = loggerSpy.debug.calls.mostRecent().args;
    expect(message).toContain('GET');
    expect(message).toContain('/api/health');
    expect(message).toContain('200');
    expect((meta as { durationMs: number }).durationMs).toBeGreaterThanOrEqual(0);
  });

  it('logs a failed response at warn, not debug', () => {
    http.get('/api/chat/history').subscribe({ error: () => {} });

    const req = httpMock.expectOne('/api/chat/history');
    req.flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(loggerSpy.warn).toHaveBeenCalledTimes(1);
    expect(loggerSpy.debug).not.toHaveBeenCalled();
    const [message] = loggerSpy.warn.calls.mostRecent().args;
    expect(message).toContain('401');
  });

  it('never logs request or response bodies, only safe metadata', () => {
    http.post('/api/auth/login', { email: 'user@example.com', password: 'super-secret' }).subscribe();

    const req = httpMock.expectOne('/api/auth/login');
    req.flush({ accessToken: 'header.payload.signature' });

    const [message, meta] = loggerSpy.debug.calls.mostRecent().args;
    expect(message).not.toContain('super-secret');
    expect(message).not.toContain('header.payload.signature');
    expect(Object.keys(meta as object)).toEqual(['durationMs', 'requestId']);
  });
});
