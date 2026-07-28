export const environment = {
  production: true,
  apiBaseUrl: 'http://localhost:8080',
  // 'warn': quiet by default in production — only unexpected conditions and
  // errors reach the browser console. Override at build time by editing this
  // file (there is no runtime env-var equivalent for a static Angular build).
  logLevel: 'warn' as const,
};
