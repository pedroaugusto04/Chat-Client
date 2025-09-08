package com.pedro.repositories;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.models.Entities.User;


@Repository
public interface UsersRepository extends JpaRepository<User, Integer> {

}
