import { Routes } from '@angular/router';
import { AppLayoutComponent } from './layout/components/app-layout/app-layout.component';
import { LoginPageComponent } from './features/auth/pages/login-page/login-page.component';
import { ChatPageComponent } from './features/chat/pages/chat-page/chat-page.component';
import { HistoryPageComponent } from './features/history/pages/history-page/history-page.component';
import { AuditPageComponent } from './features/audit/pages/audit-page/audit-page.component';
import { authGuard } from './core/guards/auth.guard';

export const routes: Routes = [
  { path: 'login', component: LoginPageComponent },
  { path: '', pathMatch: 'full', redirectTo: 'login' },
  {
    path: '',
    component: AppLayoutComponent,
    canActivate: [authGuard],
    children: [
      { path: 'chat', component: ChatPageComponent },
      { path: 'history', component: HistoryPageComponent },
      { path: 'audit', component: AuditPageComponent },
    ],
  },
  { path: '**', redirectTo: 'login' },
];
