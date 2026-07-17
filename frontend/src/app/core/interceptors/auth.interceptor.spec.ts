import { HttpTestingController, provideHttpClientTesting } from '@angular/common/http/testing';
import { HttpClient, provideHttpClient, withInterceptors } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { authInterceptor } from './auth.interceptor';
import { AuthService } from '../services/auth.service';

describe('authInterceptor', () => {
  let http: HttpClient;
  let httpMock: HttpTestingController;
  let authServiceSpy: jasmine.SpyObj<AuthService>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['getToken', 'isAuthenticated', 'logout']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        provideHttpClient(withInterceptors([authInterceptor])),
        provideHttpClientTesting(),
      ],
    });

    http = TestBed.inject(HttpClient);
    httpMock = TestBed.inject(HttpTestingController);
  });

  afterEach(() => {
    httpMock.verify();
  });

  it('attaches the Authorization header when a token exists', () => {
    authServiceSpy.getToken.and.returnValue('abc.def.ghi');

    http.get('/api/audit').subscribe();

    const req = httpMock.expectOne('/api/audit');
    expect(req.request.headers.get('Authorization')).toBe('Bearer abc.def.ghi');
    req.flush({});
  });

  it('sends no Authorization header when there is no token', () => {
    authServiceSpy.getToken.and.returnValue(null);

    http.get('/api/health').subscribe();

    const req = httpMock.expectOne('/api/health');
    expect(req.request.headers.has('Authorization')).toBeFalse();
    req.flush({});
  });

  it('logs out on a 401 from an authenticated session', () => {
    authServiceSpy.getToken.and.returnValue('expired.token.here');
    authServiceSpy.isAuthenticated.and.returnValue(true);

    http.get('/api/audit').subscribe({ error: () => {} });

    const req = httpMock.expectOne('/api/audit');
    req.flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).toHaveBeenCalled();
  });

  it('does not log out on a 401 while already unauthenticated (e.g. bad login attempt)', () => {
    authServiceSpy.getToken.and.returnValue(null);
    authServiceSpy.isAuthenticated.and.returnValue(false);

    http.post('/api/auth/login', {}).subscribe({ error: () => {} });

    const req = httpMock.expectOne('/api/auth/login');
    req.flush({}, { status: 401, statusText: 'Unauthorized' });

    expect(authServiceSpy.logout).not.toHaveBeenCalled();
  });
});
