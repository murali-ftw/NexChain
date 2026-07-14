package com.nexchain.backend.history.exception;

/**
 * Thrown when a conversation id doesn't exist, or doesn't belong to the requesting user —
 * {@code GlobalExceptionHandler} maps this to a 404 without distinguishing the two cases.
 */
public class HistoryNotFoundException extends RuntimeException {
    public HistoryNotFoundException(String id) {
        super("No conversation history found for id: " + id);
    }
}
