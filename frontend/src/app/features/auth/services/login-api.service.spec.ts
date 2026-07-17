import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { provideHttpClient } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { environment } from '../../../../environments/environment';
import { LoginApiService } from './login-api.service';
import { LoginResponse } from '../../../core/models/auth.model';

describe('LoginApiService', () => {
  let service: LoginApiService;
  let httpMock: HttpTestingController;

  beforeEach(() => {
    TestBed.configureTestingModule({
      providers: [provideHttpClient(), provideHttpClientTesting()],
    });
    service = TestBed.inject(LoginApiService);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('posts email and password to /api/auth/login', () => {
    let result: LoginResponse | undefined;
    service.login({ email: 'user@example.com', password: 'password' }).subscribe((r) => (result = r));

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/auth/login`);
    expect(req.request.method).toBe('POST');
    expect(req.request.body).toEqual({ email: 'user@example.com', password: 'password' });

    const mockResponse: LoginResponse = {
      accessToken: 'header.payload.signature',
      refreshToken: null,
      tokenType: 'Bearer',
      expiresIn: 3600,
      user: { id: 1, username: 'demo-user', email: 'user@example.com', role: 'USER' },
    };
    req.flush(mockResponse);

    expect(result).toEqual(mockResponse);
  });

  it('surfaces the backend error message on invalid credentials (401)', () => {
    let caught: unknown;
    service.login({ email: 'user@example.com', password: 'wrong' }).subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/auth/login`);
    req.flush(
      {
        timestamp: new Date().toISOString(),
        status: 401,
        error: 'Unauthorized',
        message: 'Invalid email or password',
        path: '/api/auth/login',
      },
      { status: 401, statusText: 'Unauthorized' },
    );

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('Invalid email or password');
  });

  it('falls back to a generic message when the backend is unreachable', () => {
    let caught: unknown;
    service.login({ email: 'user@example.com', password: 'password' }).subscribe({ error: (e) => (caught = e) });

    const req = httpMock.expectOne(`${environment.apiBaseUrl}/api/auth/login`);
    req.error(new ProgressEvent('error'));

    expect(caught).toBeInstanceOf(Error);
    expect((caught as Error).message).toBe('Unable to sign in. Please try again.');
  });
});
