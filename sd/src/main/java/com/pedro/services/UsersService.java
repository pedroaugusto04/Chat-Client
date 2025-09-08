package com.pedro.services;

import com.models.DTO.UserDTO;
import com.models.Entities.User;
import com.pedro.repositories.UsersRepository;

public class UsersService {
    
    private UsersRepository usersRepository;

    UsersService(UsersRepository usersRepository) {
        this.usersRepository = usersRepository;
    }

    public User getUser(Integer userId) {
        return this.usersRepository.findById(userId).orElseThrow(() -> new RuntimeException());
    }
    
    public void createUser(UserDTO userDTO) {
        
        User user = new User(userDTO.nickname());

        this.usersRepository.save(user);
    }
}
