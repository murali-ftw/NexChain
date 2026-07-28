import { bootstrapApplication } from '@angular/platform-browser';
import { appConfig } from './app/app.config';
import { AppComponent } from './app/app.component';

// The one sanctioned console.error in this app: if bootstrap itself fails,
// Angular's DI container never came up, so LoggerService (which every other
// error path in the app uses) isn't available to log through.
bootstrapApplication(AppComponent, appConfig)
  // eslint-disable-next-line no-console
  .catch((err) => console.error('Application bootstrap failed', err));
