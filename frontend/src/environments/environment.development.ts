export const environment = {
  production: false,
  apiBaseUrl: 'http://localhost:8080',
  // 'debug': verbose logging for local development (ng serve). Safe to enable
  // here since this file never ships in a production build (angular.json's
  // fileReplacements swaps it out) — see README.md "Logging" for how the two
  // environment files map to build configurations.
  logLevel: 'debug' as const,
};
