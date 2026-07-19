package com.nexchain.backend.audit.store;

import com.nexchain.backend.audit.entity.AuditEntity;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

/** Audit is a global, admin-facing log (docs/api_contracts.md) — unlike conversation
 * history, entries aren't scoped per requesting user. Access itself is restricted to
 * {@code ROLE_ADMIN} at the security-filter-chain level ({@code SecurityConfig}'s
 * {@code requestMatchers("/api/audit/**").hasRole("ADMIN")}), added after the Day 8
 * task's original "Do NOT add RBAC" deferral. */
public interface AuditRepository extends JpaRepository<AuditEntity, Long> {

    List<AuditEntity> findAllByOrderByCreatedAtDesc();

    Page<AuditEntity> findAllByOrderByCreatedAtDesc(Pageable pageable);
}
