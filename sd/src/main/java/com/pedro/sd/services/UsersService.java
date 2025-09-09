package com.pedro.sd.services;

import org.springframework.stereotype.Service;

import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.models.Entities.User;
import com.pedro.sd.repositories.UsersRepository;
import java.time.LocalDateTime;

@Service
public class UsersService {
    
    private UsersRepository usersRepository;

    UsersService(UsersRepository usersRepository) {
        this.usersRepository = usersRepository;
    }

    public User getUser(Integer userId) {
        return this.usersRepository.findById(userId).orElseThrow(() -> new RuntimeException());
    }

    public User getUserByNickname(String nickname) {
        return this.usersRepository.findByNickname(nickname).orElseThrow(() -> new RuntimeException());
    }
    
    public void createUser(UserDTO userDTO) {

        User user = this.usersRepository.findByNickname(userDTO.nickname()).orElse(null);

        if (user == null) {
            user = new User(userDTO.nickname(),userDTO.timestampClient());
        }

        user.setTimestampClient(userDTO.timestampClient());

        this.usersRepository.save(user);
    }

    public void updateUserLastActivity(User user, LocalDateTime date) {

        user.setTimestampClient(date);

        this.usersRepository.save(user);
    }
}
