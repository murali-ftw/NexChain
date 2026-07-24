package com.nexchain.backend.auth.dto;

/**
 * {@code accessToken} is a real signed JWT, issued by Spring Security (P1.6, Day 6).
 */
public record LoginResponse(
        String accessToken, String refreshToken, String tokenType, long expiresIn, UserSummary user) {}
