package com.nexchain.backend.auth.user;

/** Domain user record. {@code passwordHash} is always BCrypt — never a plaintext password. */
public record UserAccount(long id, String username, String email, String passwordHash, String role) {}
