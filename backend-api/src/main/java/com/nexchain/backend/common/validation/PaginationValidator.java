package com.nexchain.backend.common.validation;

import com.nexchain.backend.common.exception.InvalidPaginationException;

/**
 * Shared `page`/`size` validation for every paginated GET endpoint (history, audit).
 * Extracted after an audit found the first, inline copy of this check (History's) missing
 * — annotation-driven validation (`@Min`/`@Validated`) didn't reliably route through the
 * expected exception type in this Spring Boot version, so invalid params fell through to
 * a generic 500 instead of a 400. Centralizing it means that fix (and any future one)
 * only has to happen once.
 */
public final class PaginationValidator {

    private PaginationValidator() {}

    /** No-op if both are omitted (unbounded response, unchanged from before pagination
     * existed). Otherwise `page` must be >= 0 and `size` must be >= 1. */
    public static void validate(Integer page, Integer size) {
        if (page != null && page < 0) {
            throw new InvalidPaginationException("page must be >= 0");
        }
        if (size != null && size < 1) {
            throw new InvalidPaginationException("size must be >= 1");
        }
    }
}
