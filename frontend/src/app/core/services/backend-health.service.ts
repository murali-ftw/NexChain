import { HttpClient } from '@angular/common/http';
import { Injectable } from '@angular/core';
import { Observable } from 'rxjs';
import { environment } from '../../../environments/environment';

export interface HealthResponse {
  status: string;
  service: string;
}

/** Day 2: proves Angular can reach Spring Boot. See docs/api_contracts.md. */
@Injectable({ providedIn: 'root' })
export class BackendHealthService {
  constructor(private readonly http: HttpClient) {}

  checkHealth(): Observable<HealthResponse> {
    return this.http.get<HealthResponse>(`${environment.apiBaseUrl}/api/health`);
  }
}
