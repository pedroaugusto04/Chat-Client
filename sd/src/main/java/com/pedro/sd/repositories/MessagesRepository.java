package com.pedro.sd.repositories;

import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface MessagesRepository extends JpaRepository<Message, Integer> {

    Optional<Message> findByIdemKey(String idemKey);

    Optional<Message> findByIdemKeyAndDateBetween(
            String idemKey,
            LocalDateTime start,
            LocalDateTime end
    );

    List<Message> findByGroupAndDateAfterOrderByDateDesc(Group group, LocalDateTime since, Pageable pageable);

    List<Message> findByGroupOrderByDateDesc(Group group, Pageable pageable);
}