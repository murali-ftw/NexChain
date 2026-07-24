import { Component, signal } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { Router, provideRouter } from '@angular/router';
import { of } from 'rxjs';
import { AuthService } from '../../../core/services/auth.service';
import { BackendHealthService } from '../../../core/services/backend-health.service';
import { SidebarComponent } from './sidebar.component';

@Component({ standalone: true, template: '' })
class BlankPageComponent {}

/** Real Router, real RouterLinkActive — the indicator's index comes from the
 * directive, so a stubbed router would not exercise the thing under test. */
async function setup(role: string) {
  const currentUser = signal({ username: 'ada', role } as never);

  TestBed.configureTestingModule({
    imports: [SidebarComponent],
    providers: [
      provideRouter([
        { path: 'chat', component: BlankPageComponent },
        { path: 'history', component: BlankPageComponent },
        { path: 'audit', component: BlankPageComponent },
        { path: 'settings', component: BlankPageComponent },
      ]),
      { provide: BackendHealthService, useValue: { checkHealth: () => of({}) } },
      { provide: AuthService, useValue: { currentUser, logout: jasmine.createSpy('logout') } },
    ],
  });

  const router = TestBed.inject(Router);
  const fixture = TestBed.createComponent(SidebarComponent);
  fixture.detectChanges();

  const goTo = async (url: string) => {
    await router.navigate([url]);
    fixture.detectChanges();
  };

  return { fixture, component: fixture.componentInstance, goTo };
}

describe('SidebarComponent', () => {
  afterEach(() => {
    localStorage.removeItem('nexchain.sidebar.collapsed');
    TestBed.resetTestingModule();
  });

  it('hides the Audit item from non-admins', async () => {
    const { component } = await setup('USER');
    expect(component.navItems().map((item) => item.path)).toEqual(['/chat', '/history']);
  });

  it('shows the Audit item to admins', async () => {
    const { component } = await setup('ADMIN');
    expect(component.navItems().map((item) => item.path)).toEqual(['/chat', '/history', '/audit']);
  });

  it('tracks the active nav index across navigation', async () => {
    const { component, goTo } = await setup('ADMIN');

    await goTo('/chat');
    expect(component.activeIndex()).toBe(0);

    await goTo('/audit');
    expect(component.activeIndex()).toBe(2);

    await goTo('/history');
    expect(component.activeIndex()).toBe(1);
  });

  // The indicator's offset is pure CSS driven by this custom property, so the
  // binding actually reaching the DOM is the thing that can silently break.
  it('publishes the active index to CSS as --nav-active', async () => {
    const { fixture, goTo } = await setup('ADMIN');
    const nav = (fixture.nativeElement as HTMLElement).querySelector('nav') as HTMLElement;

    await goTo('/history');
    expect(nav.style.getPropertyValue('--nav-active')).toBe('1');

    await goTo('/audit');
    expect(nav.style.getPropertyValue('--nav-active')).toBe('2');
  });

  it('persists the collapsed state across reloads', async () => {
    const { component } = await setup('USER');
    expect(component.collapsed()).toBe(false);

    component.toggleCollapsed();
    expect(component.collapsed()).toBe(true);
    expect(localStorage.getItem('nexchain.sidebar.collapsed')).toBe('true');
  });
});
