import { TestBed } from '@angular/core/testing';
import { LOG_LEVEL, LoggerService } from './logger.service';

describe('LoggerService', () => {
  function serviceAtLevel(level: 'debug' | 'info' | 'warn' | 'error'): LoggerService {
    TestBed.configureTestingModule({
      providers: [{ provide: LOG_LEVEL, useValue: level }],
    });
    return TestBed.inject(LoggerService);
  }

  it('suppresses debug and info below a warn threshold', () => {
    const service = serviceAtLevel('warn');
    spyOn(console, 'log');
    spyOn(console, 'info');

    service.debug('diagnostic detail');
    service.info('normal activity');

    expect(console.log).not.toHaveBeenCalled();
    expect(console.info).not.toHaveBeenCalled();
  });

  it('emits warn and error at a warn threshold', () => {
    const service = serviceAtLevel('warn');
    spyOn(console, 'warn');
    spyOn(console, 'error');

    service.warn('recoverable condition');
    service.error('failure', { code: 500 });

    expect(console.warn).toHaveBeenCalledWith('[WARN] recoverable condition');
    expect(console.error).toHaveBeenCalledWith('[ERROR] failure', { code: 500 });
  });

  it('emits everything, including debug, at a debug threshold', () => {
    const service = serviceAtLevel('debug');
    spyOn(console, 'log');

    service.debug('diagnostic detail');

    expect(console.log).toHaveBeenCalledWith('[DEBUG] diagnostic detail');
  });

  it('suppresses everything below error at an error threshold', () => {
    const service = serviceAtLevel('error');
    spyOn(console, 'warn');
    spyOn(console, 'info');
    spyOn(console, 'log');

    service.warn('should not print');
    service.info('should not print');
    service.debug('should not print');

    expect(console.warn).not.toHaveBeenCalled();
    expect(console.info).not.toHaveBeenCalled();
    expect(console.log).not.toHaveBeenCalled();
  });
});
