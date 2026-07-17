package com.nexchain.backend.history.store;

import com.nexchain.backend.history.entity.ConversationEntity;
import java.util.List;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

public interface ConversationHistoryRepository extends JpaRepository<ConversationEntity, String> {

    List<ConversationEntity> findByUserEmailOrderByLastUpdatedDesc(String userEmail);

    Page<ConversationEntity> findByUserEmailOrderByLastUpdatedDesc(String userEmail, Pageable pageable);

    long countByUserEmail(String userEmail);
}
