package com.nexchain.backend.auth.dto;

/**
 * Day 2 contract stub. {@code accessToken} is a fixed literal, not a real JWT —
 * Spring Security / JWT issuance is P1.6 (Day 6), not today.
 */
public record LoginResponse(
        String accessToken, String refreshToken, String tokenType, long expiresIn, UserSummary user) {}
