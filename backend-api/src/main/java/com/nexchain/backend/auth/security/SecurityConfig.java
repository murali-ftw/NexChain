package com.nexchain.backend.auth.security;

import com.nexchain.backend.common.logging.RequestCorrelationFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.Customizer;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.annotation.web.configurers.AbstractHttpConfigurer;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Stateless JWT security: no HttpSession, no CSRF (there's no session cookie
 * to forge), and CORS is delegated to the existing {@code CorsConfig}
 * ({@code WebMvcConfigurer}) rather than duplicated here — Spring Security's
 * {@code cors(Customizer.withDefaults())} picks that up automatically via
 * {@code HandlerMappingIntrospector} when no {@code CorsConfigurationSource}
 * bean is defined.
 *
 * No {@code DaoAuthenticationProvider} bean is declared here: with a
 * {@link com.nexchain.backend.auth.user.AppUserDetailsService} and a
 * {@link PasswordEncoder} bean both present, Spring Boot's
 * {@code InitializeUserDetailsBeanManagerConfigurer} wires one automatically.
 *
 * {@code /api/chat/**} covers both POST /api/chat and GET /api/chat/history
 * (HistoryController is nested under that path per the frozen contract —
 * see docs/api_contracts.md).
 */
@Configuration
@EnableWebSecurity
public class SecurityConfig {

    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration configuration) throws Exception {
        return configuration.getAuthenticationManager();
    }

    @Bean
    public SecurityFilterChain securityFilterChain(
            HttpSecurity http,
            RequestCorrelationFilter requestCorrelationFilter,
            JwtAuthenticationFilter jwtAuthenticationFilter,
            RestAuthenticationEntryPoint authenticationEntryPoint,
            RestAccessDeniedHandler accessDeniedHandler)
            throws Exception {
        http.csrf(AbstractHttpConfigurer::disable)
                .cors(Customizer.withDefaults())
                .sessionManagement(sm -> sm.sessionCreationPolicy(SessionCreationPolicy.STATELESS))
                .authorizeHttpRequests(
                        auth ->
                                auth.requestMatchers("/api/auth/login", "/api/health")
                                        .permitAll()
                                        .requestMatchers("/api/audit/**")
                                        .hasRole("ADMIN")
                                        .anyRequest()
                                        .authenticated())
                .exceptionHandling(
                        ex ->
                                ex.authenticationEntryPoint(authenticationEntryPoint)
                                        .accessDeniedHandler(accessDeniedHandler))
                // jwtAuthenticationFilter must be registered (anchored to a filter class Spring
                // Security's FilterOrderRegistration already knows) before it can itself be used
                // as the anchor below — reversing these two calls fails at startup with "The
                // Filter class JwtAuthenticationFilter does not have a registered order".
                .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class)
                // Correlation id must be resolved before authentication, so it's set even for
                // requests that end up 401/403 — every response, success or failure, carries
                // an X-Request-ID and every log line for the request (including the auth
                // filter's own) has it in MDC.
                .addFilterBefore(requestCorrelationFilter, JwtAuthenticationFilter.class);
        return http.build();
    }
}
