import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { of, throwError } from 'rxjs';
import { LoginPageComponent } from './login-page.component';
import { AuthService } from '../../../../core/services/auth.service';

describe('LoginPageComponent', () => {
  let component: LoginPageComponent;
  let authServiceSpy: jasmine.SpyObj<AuthService>;
  let routerSpy: jasmine.SpyObj<Router>;

  beforeEach(() => {
    authServiceSpy = jasmine.createSpyObj('AuthService', ['login']);
    routerSpy = jasmine.createSpyObj('Router', ['navigate']);

    TestBed.configureTestingModule({
      imports: [LoginPageComponent],
      providers: [
        { provide: AuthService, useValue: authServiceSpy },
        { provide: Router, useValue: routerSpy },
      ],
    });

    component = TestBed.createComponent(LoginPageComponent).componentInstance;
  });

  it('navigates to /chat on successful login', () => {
    authServiceSpy.login.and.returnValue(of({ id: 1, username: 'demo-user', email: 'user@example.com', role: 'USER' }));
    component.email = 'user@example.com';
    component.password = 'password';

    component.onSignIn();

    expect(authServiceSpy.login).toHaveBeenCalledWith('user@example.com', 'password');
    expect(routerSpy.navigate).toHaveBeenCalledWith(['/chat']);
    expect(component.errorMessage()).toBeNull();
    expect(component.submitting()).toBeFalse();
  });

  it('shows an inline error and does not navigate on invalid credentials', () => {
    authServiceSpy.login.and.returnValue(throwError(() => new Error('Invalid email or password')));
    component.email = 'user@example.com';
    component.password = 'wrong-password';

    component.onSignIn();

    expect(routerSpy.navigate).not.toHaveBeenCalled();
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
