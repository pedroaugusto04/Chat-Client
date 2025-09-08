package com.pedro.repositories;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;

import com.models.Entities.Group;
import com.models.Entities.Message;

public interface MessagesRepository extends JpaRepository<Message, Integer> {

    List<Message> findByGroupAndCreatedAtAfterOrderByCreatedAtAsc(Group group, LocalDateTime since, Pageable pageable);

    List<Message> findByGroupOrderByCreatedAtDesc(Group group, Pageable pageable);
}