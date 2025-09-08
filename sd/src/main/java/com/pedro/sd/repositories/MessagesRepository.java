package com.pedro.sd.repositories;

import java.time.LocalDateTime;
import java.util.List;

import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;

@Repository
public interface MessagesRepository extends JpaRepository<Message, Integer> {

    List<Message> findByGroupAndDateAfterOrderByDateAsc(Group group, LocalDateTime since, Pageable pageable);

    List<Message> findByGroupOrderByDateDesc(Group group, Pageable pageable);
}