package com.nexchain.backend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.CorsRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

/**
 * Local-dev CORS: Angular (ng serve, localhost:4200) and Spring Boot (localhost:8080)
 * run as two separate origins, so the browser blocks fetch/XHR between them unless
 * the server opts in explicitly. Configured here (rather than an Angular proxy) so
 * the allowed origin is visible and enforced on the server that will eventually sit
 * behind a real gateway in every environment, not just local dev.
 *
 * Origin list is a property, not a wildcard, per docs/02_technical_requirements.md
 * Section 8 (no permissive CORS).
 */
@Configuration
public class CorsConfig implements WebMvcConfigurer {

    @Value("${app.cors.allowed-origins}")
    private String[] allowedOrigins;

    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
                .allowedOrigins(allowedOrigins)
                .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
                .allowedHeaders("*");
    }
}
