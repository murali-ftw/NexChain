package com.nexchain.backend.auth.user;

import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

/**
 * Day 6 (P1.6) stand-in for Person 2's {@code users} table
 * (docs/06_backend_schema.md Section 2.13), which isn't wired into Spring
 * Boot yet — no JPA/JDBC dependency has been added. Seeded with the same
 * demo account the Day 2 {@code mockLogin} stub used
 * ({@code user@example.com} / {@code password}) so existing manual/demo
 * flows keep working once real authentication replaces the stub.
 *
 * <p>The three passwords default to {@code "password"} for local/demo use but
 * are overridable via {@code app.demo-users.*} (env vars {@code DEMO_USER_PASSWORD},
 * {@code DEMO_SECOND_USER_PASSWORD}, {@code DEMO_ADMIN_PASSWORD}) — see
 * "Known Limitations" in the README. Override the admin password at minimum
 * before exposing this service outside local development, since these
 * defaults are public in this repository.
 */
@Component
public class InMemoryUserStore implements UserStore {

    private final Map<String, UserAccount> byEmail = new ConcurrentHashMap<>();

    public InMemoryUserStore(
            PasswordEncoder passwordEncoder,
            @Value("${app.demo-users.user-password:password}") String userPassword,
            @Value("${app.demo-users.second-user-password:password}") String secondUserPassword,
            @Value("${app.demo-users.admin-password:password}") String adminPassword) {
        UserAccount demoUser =
                new UserAccount(1L, "demo-user", "user@example.com", passwordEncoder.encode(userPassword), "USER");
        byEmail.put(demoUser.email(), demoUser);

        // P1.7: a second account so history isolation ("users must only access their own
        // conversations") is actually exercisable, not just asserted against a single user.
        UserAccount secondUser =
                new UserAccount(
                        2L,
                        "second-user",
                        "second-user@example.com",
                        passwordEncoder.encode(secondUserPassword),
                        "USER");
        byEmail.put(secondUser.email(), secondUser);

        // RC stabilization: the audit log is admin-only (SecurityConfig, "/api/audit/**"
        // hasRole("ADMIN")) — seeded here so that RBAC is actually exercisable end-to-end,
        // not just enforced against an account nothing can authenticate as.
        UserAccount adminUser =
                new UserAccount(
                        3L, "admin-user", "admin@example.com", passwordEncoder.encode(adminPassword), "ADMIN");
        byEmail.put(adminUser.email(), adminUser);
    }

    @Override
    public Optional<UserAccount> findByEmail(String email) {
        return Optional.ofNullable(byEmail.get(email));
    }
}
