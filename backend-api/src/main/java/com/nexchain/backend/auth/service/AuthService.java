package com.nexchain.backend.auth.service;

import com.nexchain.backend.auth.dto.LoginRequest;
import com.nexchain.backend.auth.dto.LoginResponse;
import com.nexchain.backend.auth.dto.UserSummary;
import org.springframework.stereotype.Service;

/**
 * Day 2 contract stub — no password hashing, no user store, no JWT.
 * Real authentication is P1.6 (Day 6).
 */
@Service
public class AuthService {

    public LoginResponse mockLogin(LoginRequest request) {
        var user = new UserSummary(1L, "demo-user", request.email(), "USER");
        return new LoginResponse("mock-token", null, "Bearer", 3600, user);
    }
}
