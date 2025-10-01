package com.pedro.sd.repositories;

import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.time.OffsetDateTime;
import java.util.List;
import java.util.Optional;

@Repository
public interface MessagesRepository extends JpaRepository<Message, Integer> {

    Optional<Message> findByIdemKey(String idemKey);

    Optional<Message> findByIdemKeyAndClientDateBetween(
            String idemKey,
            OffsetDateTime start,
            OffsetDateTime end
    );

    List<Message> findByGroupAndClientDateAfterOrderByClientDateDesc(Group group, OffsetDateTime since, Pageable pageable);

    List<Message> findByGroupOrderByClientDateDesc(Group group, Pageable pageable);
}