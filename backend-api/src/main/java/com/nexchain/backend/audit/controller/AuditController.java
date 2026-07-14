package com.nexchain.backend.audit.controller;

import com.nexchain.backend.audit.dto.AuditEntryDto;
import com.nexchain.backend.audit.service.AuditService;
import com.nexchain.backend.common.validation.PaginationValidator;
import java.util.List;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

/** Global, admin-facing audit log (docs/api_contracts.md). Both endpoints already require
 * JWT authentication (SecurityConfig's default {@code anyRequest().authenticated()}); a
 * role check restricting this to admins is explicitly deferred (Day 8 "Do NOT add RBAC"). */
@RestController
@RequestMapping("/api/audit")
public class AuditController {

    /** Only used when the caller supplies `page` without `size` — pagination is opt-in;
     * omitting both params keeps the original unbounded response (mirrors GET
     * /api/chat/history, P1.7 rectification). */
    private static final int DEFAULT_PAGE_SIZE = 20;

    private final AuditService auditService;

    public AuditController(AuditService auditService) {
        this.auditService = auditService;
    }

    /** Omitting both `page` and `size` returns every entry, exactly as before. Supplying
     * either one opts into paging; `X-Total-Count` always reports the total. */
    @GetMapping
    public ResponseEntity<List<AuditEntryDto>> getAuditLog(
            @RequestParam(required = false) Integer page, @RequestParam(required = false) Integer size) {
        PaginationValidator.validate(page, size);

        List<AuditEntryDto> entries =
                (page == null && size == null)
                        ? auditService.getAuditLog()
                        : auditService.getAuditLog(page != null ? page : 0, size != null ? size : DEFAULT_PAGE_SIZE);
        long total = auditService.countAuditLog();
        return ResponseEntity.ok().header("X-Total-Count", String.valueOf(total)).body(entries);
    }

    @GetMapping("/{id}")
    public AuditEntryDto getAuditEntry(@PathVariable long id) {
        return auditService.getAuditEntry(id);
    }
}
