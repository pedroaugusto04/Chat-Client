package com.pedro.sd.services;

import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import com.pedro.sd.models.Entities.User;
import com.pedro.sd.repositories.MessagesRepository;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.time.ZoneId;
import java.util.Date;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class MessagesService {

    private MessagesRepository messagesRepository;
    private com.pedro.sd.services.UsersService usersService;
    private com.pedro.sd.services.GroupsService groupsService;
    private LogsService logsService;

    MessagesService(com.pedro.sd.services.UsersService usersService, com.pedro.sd.services.GroupsService groupsService, MessagesRepository messagesRepository,
                    LogsService logsService) {
        this.messagesRepository = messagesRepository;
        this.usersService = usersService;
        this.groupsService = groupsService;
        this.logsService = logsService;
    }

    public void sendMessage(Integer groupId, MessageSendDTO messageDTO) {

        Message processedMessage = this.messagesRepository.findByIdemKey(messageDTO.idemKey()).orElse(null);

        /* caso a mensagem com mesma chave de idempotencia ja tenha sido processada, nao processa novamente
        */
        if (processedMessage != null) {
            this.logsService.log(messageDTO, "MESSAGE_ALREADY_PROCESSED", "Mensagem ja processada");
            return;
        }

        User user = this.usersService.getUserByNickname(messageDTO.userNickname());

        Group group = this.groupsService.getGroup(groupId);

        Message message = new Message(messageDTO.text(), user, group, messageDTO.idemKey(), messageDTO.timestampClient());

        this.messagesRepository.save(message);

        this.usersService.updateUserLastActivity(user, messageDTO.timestampClient());
    }

    public List<MessageResponseDTO> getMessages(Integer groupId, Date since, Integer limit) {
        Group group = this.groupsService.getGroup(groupId);

        List<Message> messages;

        if (since != null) {
            LocalDateTime sinceDateTime = LocalDateTime.ofInstant(since.toInstant(), ZoneId.systemDefault());
            messages = messagesRepository.findByGroupAndDateAfterOrderByDateDesc(
                    group,
                    sinceDateTime,
                    PageRequest.of(0, limit));
        } else {
            messages = messagesRepository.findByGroupOrderByDateDesc(
                    group,
                    PageRequest.of(0, limit));
        }

       return messages.stream()
        .map(m -> new MessageResponseDTO(m.getIdemKey(),m.getText(), m.getUser().getId(), m.getUser().getNickname(),m.getDate(),null))
        .collect(Collectors.toList());

    }
}
