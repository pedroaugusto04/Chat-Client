package com.pedro.sd.controllers;

import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.services.LogsService;
import com.pedro.sd.services.MessagesService;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import java.time.OffsetDateTime;



@RestController
public class MessagesController {

    private MessagesService messagesService;
    private LogsService logsService;

    MessagesController(MessagesService messagesService, LogsService logsService, SimpMessagingTemplate messagingTemplate) {
        this.messagesService = messagesService;
        this.logsService = logsService;
    }

    @MessageMapping("/chat/{groupId}")
    @SendTo("/topic/messages.{groupId}")
    public void connectToGroup(@DestinationVariable Long groupId, UserDTO userDTO) {
        this.logsService.log(userDTO, "GROUP_CONNECT", userDTO.nickname() + " conectou no grupo WEB SOCKET " + groupId);
    }

    @PostMapping("/chat/{groupId}/messages")
    public void sendMessageWS(@PathVariable Integer groupId,
                              @RequestBody MessageSendDTO messageDTO) throws InterruptedException {

        long startTime = System.currentTimeMillis();

        messageDTO.setTimestampClient(OffsetDateTime.now()); 

        this.logsService.log(messageDTO, "SEND_MESSAGE_WS",
                "Entrou no endpoint para envio de mensagem");

        // tenta publicar a mensagem na fila
        messagesService.publishMessageToKafka(groupId, messageDTO);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(messageDTO, "SEND_MESSAGE_WS", "Iniciou tentativa de publicacao na fila em " + latency + " ms");
    }

}