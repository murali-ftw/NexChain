import { TestBed } from '@angular/core/testing';
import { Router, UrlTree } from '@angular/router';
import { adminGuard } from './admin.guard';
import { AuthService } from '../services/auth.service';
import { AuthUser } from '../models/auth.model';

describe('adminGuard', () => {
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', [], { currentUser: () => null });
    routerSpy = jasmine.createSpyObj('Router', ['createUrlTree']);

    TestBed.configureTestingModule({
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });
  });

  function withUser(role: string | undefined): void {
    const user = role ? ({ id: 1, username: 'u', email: 'u@example.com', role } as AuthUser) : null;
    Object.defineProperty(authServiceSpy, 'currentUser', { value: () => user });
  }

  it('allows navigation for an ADMIN user', () => {
    withUser('ADMIN');

    const result = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));

    expect(result).toBeTrue();
  });

  it('redirects a non-admin user to /chat', () => {
    withUser('USER');
    const urlTree = {} as UrlTree;
    routerSpy.createUrlTree.and.returnValue(urlTree);

    const result = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));

    expect(routerSpy.createUrlTree).toHaveBeenCalledWith(['/chat']);
    expect(result).toBe(urlTree);
  });

  it('redirects when there is no current user', () => {
    withUser(undefined);
    const urlTree = {} as UrlTree;
    routerSpy.createUrlTree.and.returnValue(urlTree);

    const result = TestBed.runInInjectionContext(() => adminGuard({} as never, {} as never));

    expect(result).toBe(urlTree);
  });
});
