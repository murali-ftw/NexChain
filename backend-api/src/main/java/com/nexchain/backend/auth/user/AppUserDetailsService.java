package com.nexchain.backend.auth.user;

import org.springframework.security.core.userdetails.User;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

/** Bridges {@link UserStore} to Spring Security. The "username" it looks up by is the login email. */
@Service
public class AppUserDetailsService implements UserDetailsService {

    private final UserStore userStore;

    public AppUserDetailsService(UserStore userStore) {
        this.userStore = userStore;
    }

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        UserAccount account =
                userStore
                        .findByEmail(email)
                        .orElseThrow(() -> new UsernameNotFoundException("No user with email " + email));
        return User.withUsername(account.email())
                .password(account.passwordHash())
                .authorities("ROLE_" + account.role())
                .build();
    }
}
