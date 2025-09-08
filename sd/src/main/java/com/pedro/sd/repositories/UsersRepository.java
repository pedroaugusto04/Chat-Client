package com.pedro.sd.repositories;

import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import com.pedro.sd.models.Entities.User;


@Repository
public interface UsersRepository extends JpaRepository<User, Integer> {

}
