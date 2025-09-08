package com.pedro.sd.services;

import org.springframework.stereotype.Service;

import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.models.Entities.User;
import com.pedro.sd.repositories.UsersRepository;

@Service
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
