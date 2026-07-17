import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of } from 'rxjs';
import { AuthService } from './auth.service';
import { LoginApiService } from '../../features/auth/services/login-api.service';
import { LoginResponse } from '../models/auth.model';

describe('AuthService', () => {
  let loginApiServiceSpy: jasmine.SpyObj<LoginApiService>;
  let routerSpy: jasmine.SpyObj<Router>;

  const mockResponse: LoginResponse = {
    accessToken: 'header.payload.signature',
    refreshToken: null,
    tokenType: 'Bearer',
    expiresIn: 3600,
    user: { id: 1, username: 'demo-user', email: 'user@example.com', role: 'USER' },
  };

  beforeEach(() => {
    localStorage.clear();
    loginApiServiceSpy = jasmine.createSpyObj('LoginApiService', ['login']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      providers: [
        { provide: LoginApiService, useValue: loginApiServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
  });

  afterEach(() => {
    localStorage.clear();
  });

  it('starts unauthenticated with no stored session', () => {
    const service = TestBed.inject(AuthService);
    expect(service.isAuthenticated()).toBeFalse();
    expect(service.currentUser()).toBeNull();
  });

  it('restores a session already in localStorage on construction', () => {
    localStorage.setItem('nexchain.auth.token', 'existing-token');
    localStorage.setItem('nexchain.auth.user', JSON.stringify(mockResponse.user));

    const service = TestBed.inject(AuthService);

    expect(service.isAuthenticated()).toBeTrue();
    expect(service.currentUser()).toEqual(mockResponse.user);
  });

  it('login() persists the token/user and updates state', () => {
    loginApiServiceSpy.login.and.returnValue(of(mockResponse));
    const service = TestBed.inject(AuthService);

    let emitted: unknown;
    service.login('user@example.com', 'password').subscribe((u) => (emitted = u));

    expect(emitted).toEqual(mockResponse.user);
    expect(service.isAuthenticated()).toBeTrue();
    expect(service.getToken()).toBe(mockResponse.accessToken);
    expect(localStorage.getItem('nexchain.auth.token')).toBe(mockResponse.accessToken);
    expect(JSON.parse(localStorage.getItem('nexchain.auth.user')!)).toEqual(mockResponse.user);
  });

  it('logout() clears state, storage, and redirects to /login', () => {
    loginApiServiceSpy.login.and.returnValue(of(mockResponse));
    const service = TestBed.inject(AuthService);
    service.login('user@example.com', 'password').subscribe();

    service.logout();

    expect(service.isAuthenticated()).toBeFalse();
    expect(service.currentUser()).toBeNull();
    expect(localStorage.getItem('nexchain.auth.token')).toBeNull();
    expect(localStorage.getItem('nexchain.auth.user')).toBeNull();
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/login']);
  });
});
