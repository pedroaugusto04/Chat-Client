package com.pedro.sd.services;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import com.pedro.sd.models.Entities.User;
import com.pedro.sd.repositories.MessagesRepository;

@Service
public class MessagesService {

    private MessagesRepository messagesRepository;
    private UsersService usersService;
    private GroupsService groupsService;

    MessagesService(UsersService usersService, GroupsService groupsService, MessagesRepository messagesRepository) {
        this.messagesRepository = messagesRepository;
        this.usersService = usersService;
        this.groupsService = groupsService;
    }

    public void sendMessage(Integer groupId, MessageSendDTO messageDTO) {

        User user = this.usersService.getUser(messageDTO.userId());

        Group group = this.groupsService.getGroup(groupId);

        Message message = new Message(messageDTO.text(), user, group);

        this.messagesRepository.save(message);
    }

    public List<MessageResponseDTO> getMessages(Integer groupId, Date since, Integer limit) {
        Group group = this.groupsService.getGroup(groupId);

        List<Message> messages;

        if (since != null) {
            LocalDateTime sinceDateTime = LocalDateTime.ofInstant(since.toInstant(), ZoneId.systemDefault());
            messages = messagesRepository.findByGroupAndDateAfterOrderByDateAsc(
                    group,
                    sinceDateTime,
                    PageRequest.of(0, limit));
        } else {
            messages = messagesRepository.findByGroupOrderByDateDesc(
                    group,
                    PageRequest.of(0, limit));
        }

       return messages.stream()
        .map(m -> new MessageResponseDTO(m.getText(), m.getUser().getId(), m.getDate()))
        .collect(Collectors.toList());

    }
}
