package com.nexchain.backend.auth.dto;

import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;

public record LoginRequest(
        @NotBlank(message = "email must not be blank") @Email(message = "email must be a valid address") String email,
        @NotBlank(message = "password must not be blank") String password) {}
