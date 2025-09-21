package com.pedro.sd.repositories;

import com.pedro.sd.models.Entities.Group;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.Optional;


@Repository
public interface GroupsRepository extends JpaRepository<Group, Integer> {
    Optional<Group> findByName(String name);
}
