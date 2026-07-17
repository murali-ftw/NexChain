package com.nexchain.backend.audit.exception;

/** Thrown when an audit id doesn't exist — {@code GlobalExceptionHandler} maps this to a 404. */
public class AuditEntryNotFoundException extends RuntimeException {
    public AuditEntryNotFoundException(long auditId) {
        super("No audit entry found for id: " + auditId);
    }
}
