package com.nexchain.backend.common.exception;

/** Thrown for an out-of-range `page`/`size` query param (GET /api/chat/history,
 * GET /api/audit) — {@code GlobalExceptionHandler} maps this to a 400. */
public class InvalidPaginationException extends RuntimeException {
    public InvalidPaginationException(String message) {
        super(message);
    }
}
