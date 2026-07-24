import { TestBed } from '@angular/core/testing';
import { ActivatedRoute, Router, convertToParamMap } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginPageComponent } from './login-page.component';
import { AuthService } from '../../../../core/services/auth.service';

function activatedRouteStub(queryParams: Record<string, string> = {}) {
  return { snapshot: { queryParamMap: convertToParamMap(queryParams) } };
}

describe('LoginPageComponent', () => {
  let component: LoginPageComponent;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  function setup(queryParams: Record<string, string> = {}) {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);
    routerSpy = jasmine.createSpyObj('Router', ['navigateByUrl']);

    TestBed.resetTestingModule().configureTestingModule({
      imports: [LoginPageComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
        { provide: ActivatedRoute, useValue: activatedRouteStub(queryParams) },
      ],
    });

    component = TestBed.createComponent(LoginPageComponent).componentInstance;
  }

  beforeEach(() => setup());

  it('navigates to /chat on successful login when no returnUrl is present', () => {
    authServiceSpy.login.and.returnValue(of({ id: 1, username: 'demo-user', email: 'user@example.com', role: 'USER' }));
    component.email = 'user@example.com';
    component.password = 'password';

    component.onSignIn();

    expect(authServiceSpy.login).toHaveBeenCalledWith('user@example.com', 'password');
    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/chat');
    expect(component.errorMessage()).toBeNull();
    expect(component.submitting()).toBeFalse();
  });

  it('navigates to the returnUrl on successful login when redirected by a guard', () => {
    setup({ returnUrl: '/history' });
    authServiceSpy.login.and.returnValue(of({ id: 1, username: 'demo-user', email: 'user@example.com', role: 'USER' }));
    component.email = 'user@example.com';
    component.password = 'password';

    component.onSignIn();

    expect(routerSpy.navigateByUrl).toHaveBeenCalledWith('/history');
  });

  it('shows an inline error and does not navigate on invalid credentials', () => {
    authServiceSpy.login.and.returnValue(throwError(() => new Error('Invalid email or password')));
    component.email = 'user@example.com';
    component.password = 'wrong-password';

    component.onSignIn();

    expect(routerSpy.navigateByUrl).not.toHaveBeenCalled();
    expect(component.errorMessage()).toBe('Invalid email or password');
    expect(component.submitting()).toBeFalse();
  });

  it('does not call login with a blank email or password', () => {
    component.email = '';
    component.password = '';

    component.onSignIn();

    expect(authServiceSpy.login).not.toHaveBeenCalled();
  });
});
