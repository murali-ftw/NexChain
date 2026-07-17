package com.nexchain.backend.auth.user;

import java.util.Optional;

/**
 * Abstraction over user lookup so the in-memory Day 6 implementation can be
 * swapped for Person 2's {@code users} table (docs/06_backend_schema.md
 * Section 2.13) without touching {@link AppUserDetailsService} or
 * {@code AuthService}.
 */
public interface UserStore {
    Optional<UserAccount> findByEmail(String email);
}
