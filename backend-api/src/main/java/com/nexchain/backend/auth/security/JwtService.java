package com.nexchain.backend.auth.security;

import com.nexchain.backend.auth.user.UserAccount;
import io.jsonwebtoken.Claims;
import io.jsonwebtoken.JwtException;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.time.Instant;
import java.util.Date;
import javax.crypto.SecretKey;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;

/**
 * Issues and validates self-signed, HMAC-signed JWTs. {@link Keys#hmacShaKeyFor}
 * selects HS256/HS384/HS512 based on {@code app.jwt.secret}'s byte length (HS512
 * needs >= 64 bytes) — docs/api_contracts.md's frozen login contract documents
 * HS512, so a deployed secret must be at least 64 bytes for the token to match
 * that contract. Access-token only — refresh tokens are explicitly out of scope
 * for Day 6 (docs/team_plan.md P1.6).
 */
@Service
public class JwtService {

    private static final Logger log = LoggerFactory.getLogger(JwtService.class);

    // Must match the fallback literal in application.yml's app.jwt.secret default.
    private static final String INSECURE_DEFAULT_SECRET =
            "dev-only-secret-do-not-use-in-production-replace-via-JWT_SECRET-env-var";

    private final SecretKey key;
    private final long expirationSeconds;

    public JwtService(
            @Value("${app.jwt.secret}") String secret,
            @Value("${app.jwt.expiration-seconds}") long expirationSeconds) {
        if (INSECURE_DEFAULT_SECRET.equals(secret)) {
            log.warn(
                    "app.jwt.secret is using the well-known dev-only default. Every token signed with"
                        + " it can be forged by anyone who has read this repository. Set the JWT_SECRET"
                        + " environment variable to a unique, random value before exposing this service"
                        + " outside local development.");
        }
        this.key = Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
        this.expirationSeconds = expirationSeconds;
    }

    public long expirationSeconds() {
        return expirationSeconds;
    }

    public String generateToken(UserAccount user) {
        Instant now = Instant.now();
        return Jwts.builder()
                .subject(user.email())
                .claim("uid", user.id())
                .claim("username", user.username())
                .claim("role", user.role())
                .issuedAt(Date.from(now))
                .expiration(Date.from(now.plusSeconds(expirationSeconds)))
                .signWith(key)
                .compact();
    }

    /** @throws JwtException if the token is malformed, expired, or has an invalid signature. */
    public Claims parseAndValidate(String token) {
        return Jwts.parser().verifyWith(key).build().parseSignedClaims(token).getPayload();
    }
}
