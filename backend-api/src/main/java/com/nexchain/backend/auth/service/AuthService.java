package com.nexchain.backend.auth.service;

import com.nexchain.backend.auth.dto.LoginRequest;
import com.nexchain.backend.auth.dto.LoginResponse;
import com.nexchain.backend.auth.dto.UserSummary;
import com.nexchain.backend.auth.security.JwtService;
import com.nexchain.backend.auth.user.UserAccount;
import com.nexchain.backend.auth.user.UserStore;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.stereotype.Service;

/** Day 6 (P1.6) real authentication — replaces the Day 2 {@code mockLogin} stub. */
@Service
public class AuthService {

    private final AuthenticationManager authenticationManager;
    private final UserStore userStore;
    private final JwtService jwtService;

    public AuthService(AuthenticationManager authenticationManager, UserStore userStore, JwtService jwtService) {
        this.authenticationManager = authenticationManager;
        this.userStore = userStore;
        this.jwtService = jwtService;
    }

    /**
     * @throws org.springframework.security.core.AuthenticationException if the email/password
     *     pair is invalid — handled centrally by {@code GlobalExceptionHandler} into a clean 401.
     */
    public LoginResponse login(LoginRequest request) {
        authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(request.email(), request.password()));

        // Authentication succeeded, so this lookup cannot miss — the same UserStore
        // backed AppUserDetailsService for the authenticate() call above.
        UserAccount account =
                userStore
                        .findByEmail(request.email())
                        .orElseThrow(() -> new IllegalStateException("Authenticated user vanished: " + request.email()));

        String token = jwtService.generateToken(account);
        var user = new UserSummary(account.id(), account.username(), account.email(), account.role());
        return new LoginResponse(token, null, "Bearer", jwtService.expirationSeconds(), user);
    }
}
