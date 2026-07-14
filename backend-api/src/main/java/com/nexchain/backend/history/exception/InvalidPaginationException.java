package com.nexchain.backend.history.exception;

/** Thrown for an out-of-range `page`/`size` query param on GET /api/chat/history —
 * {@code GlobalExceptionHandler} maps this to a 400. */
public class InvalidPaginationException extends RuntimeException {
    public InvalidPaginationException(String message) {
        super(message);
    }
}
