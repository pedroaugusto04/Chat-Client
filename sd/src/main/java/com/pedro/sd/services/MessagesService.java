package com.pedro.sd.services;

import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.Entities.Group;
import com.pedro.sd.models.Entities.Message;
import com.pedro.sd.models.Entities.User;
import com.pedro.sd.repositories.MessagesRepository;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Service;

@Service
public class MessagesService {

    private MessagesRepository messagesRepository;
    private com.pedro.sd.services.UsersService usersService;
    private com.pedro.sd.services.GroupsService groupsService;
    private final KafkaTemplate<String, MessageSendDTO> kafkaTemplate;
    private LogsService logsService;


    MessagesService(com.pedro.sd.services.UsersService usersService, com.pedro.sd.services.GroupsService groupsService, MessagesRepository messagesRepository,
                    LogsService logsService, KafkaTemplate<String, MessageSendDTO> kafkaTemplate) {
        this.messagesRepository = messagesRepository;
        this.usersService = usersService;
        this.groupsService = groupsService;
        this.logsService = logsService;
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendMessage(Integer groupId, MessageSendDTO messageDTO) {

        User user = this.usersService.getUserByNickname(messageDTO.getUserNickname());

        Group group = this.groupsService.getGroup(groupId);

        Message message = new Message(messageDTO.getText(), user, group, messageDTO.getIdemKey(), messageDTO.getTimestampClient());

        this.messagesRepository.save(message);

        this.usersService.updateUserLastActivity(user, messageDTO.getTimestampClient());
    }

    public void publishMessageToKafka(Integer groupId, MessageSendDTO messageSendDTO) {
        kafkaTemplate.executeInTransaction(template ->
            template.send("chat-messages", groupId.toString(),messageSendDTO));
    }
}
