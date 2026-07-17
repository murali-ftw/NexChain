package com.nexchain.backend.history.controller;

import com.nexchain.backend.common.validation.PaginationValidator;
import com.nexchain.backend.history.dto.HistoryDetailDto;
import com.nexchain.backend.history.dto.HistoryItemDto;
import com.nexchain.backend.history.service.HistoryService;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.DeleteMapping;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/**
 * Contributes GET/DELETE /api/chat/history* — nested under the chat path per the frozen
 * contract. Every method scopes to the caller's own conversations only:
 * {@code Authentication.getName()} is the JWT subject, which is the user's email (see
 * {@code AppUserDetailsService}).
 */
@RestController
@RequestMapping("/api/chat")
public class HistoryController {

    /** Only used when the caller supplies `page` without `size` (P1.7 rectification —
     * pagination is opt-in; omitting both params keeps the original unbounded response). */
    private static final int DEFAULT_PAGE_SIZE = 20;

    private final HistoryService historyService;

    public HistoryController(HistoryService historyService) {
        this.historyService = historyService;
    }

    /** Omitting both `page` and `size` returns every conversation, exactly as before —
     * existing callers (Angular's client-side search needs the full set) are unaffected.
     * Supplying either one opts into paging; `X-Total-Count` always reports the total so a
     * caller can tell how many pages exist. */
    @GetMapping("/history")
    public ResponseEntity<List<HistoryItemDto>> getHistory(
            Authentication authentication,
            @RequestParam(required = false) Integer page,
            @RequestParam(required = false) Integer size) {
        PaginationValidator.validate(page, size);

        String userEmail = authentication.getName();
        List<HistoryItemDto> items =
                (page == null && size == null)
                        ? historyService.getHistory(userEmail)
                        : historyService.getHistory(
                                userEmail, page != null ? page : 0, size != null ? size : DEFAULT_PAGE_SIZE);
        long total = historyService.countHistory(userEmail);
        return ResponseEntity.ok().header("X-Total-Count", String.valueOf(total)).body(items);
    }

    @GetMapping("/history/{id}")
    public HistoryDetailDto getHistoryDetail(Authentication authentication, @PathVariable String id) {
        return historyService.getDetail(authentication.getName(), id);
    }

    @DeleteMapping("/history/{id}")
    public ResponseEntity<Void> deleteHistory(Authentication authentication, @PathVariable String id) {
        historyService.delete(authentication.getName(), id);
        return ResponseEntity.noContent().build();
    }
}
