package com.pedro.repositories;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.models.Entities.Group;


@Repository
public interface GroupsRepository extends JpaRepository<Group, Integer> {

}
