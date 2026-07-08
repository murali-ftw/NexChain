package com.nexchain.backend.common.response;

import java.time.Instant;

/** Standard error body returned by {@link com.nexchain.backend.common.exception.GlobalExceptionHandler}. */
public record ErrorResponse(Instant timestamp, int status, String error, String message, String path) {}
