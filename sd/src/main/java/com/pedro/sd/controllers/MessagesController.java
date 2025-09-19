package com.pedro.sd.controllers;

import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.DTO.ProcessedMessageDTO;
import com.pedro.sd.models.DTO.UserDTO;
import com.pedro.sd.services.LogsService;
import com.pedro.sd.services.MessagesService;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.handler.annotation.DestinationVariable;
import org.springframework.messaging.handler.annotation.MessageMapping;
import org.springframework.messaging.handler.annotation.SendTo;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.*;

import java.util.Date;
import java.util.List;



@RestController
public class MessagesController {

    private MessagesService messagesService;
    private LogsService logsService;
    private SimpMessagingTemplate messagingTemplate;

    MessagesController(MessagesService messagesService, LogsService logsService, SimpMessagingTemplate messagingTemplate) {
        this.messagesService = messagesService;
        this.logsService = logsService;
        this.messagingTemplate = messagingTemplate;
    }

    @GetMapping("groups/{id}/messages")
    public ResponseEntity<List<MessageResponseDTO>> getLastMessages(

            @PathVariable("id") Integer groupId,
            @RequestParam(value = "since", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date since,
            @RequestParam(value = "limit", defaultValue = "10") Integer limit) {

        long startTime = System.currentTimeMillis();

        this.logsService.log(groupId, "GET_MESSAGES", "Entrou no endpoint para recuperacao de mensagens do grupo");

        List<MessageResponseDTO> messages = messagesService.getMessages(groupId, since, limit);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(messages, "GET_MESSAGES", "Recuperou com sucesso as mensagens do grupo " + groupId + " em " + latency + " ms");

        return ResponseEntity.ok(messages);
    }

    @MessageMapping("/chat/{groupId}")
    @SendTo("/topic/messages.{groupId}")
    public void connectToGroup(@DestinationVariable Long groupId, UserDTO userDTO) {
        this.logsService.log(userDTO, "GROUP_CONNECT", userDTO.nickname() + " conectou no grupo WEB SOCKET " + groupId);
    }

    @PostMapping("/chat/{groupId}/messages")
    public void sendMessageWS(@PathVariable Integer groupId, @RequestBody MessageSendDTO messageDTO
    ) {

        this.logsService.log(messageDTO, "SEND_MESSAGE_WS", "Entrou no endpoint WS para envio de mensagem");

        long startTime = System.currentTimeMillis();

        messagesService.sendMessage(groupId, messageDTO);

        long latency = System.currentTimeMillis() - startTime;

        this.logsService.log(messageDTO, "SEND_MESSAGE_WS", "Mensagem enviada via WS em " + latency + " ms");

        // envia pra todos do grupo ( somente apos salvar no banco )
        messagingTemplate.convertAndSend("/topic/messages." + groupId,
                new MessageResponseDTO(messageDTO.idemKey(),messageDTO.text(), null, messageDTO.userNickname(), messageDTO.timestampClient(), messageDTO.sentTime()));

        // confirma o processamento da mensagem
        String userNickname = messageDTO.userNickname();
        if (userNickname != null && !userNickname.isEmpty()) {
            String ackDestination = "/topic/acks." + userNickname;

            messagingTemplate.convertAndSend(ackDestination, new ProcessedMessageDTO(messageDTO.idemKey()));

            this.logsService.log(messageDTO, "SEND_ACK_MESSAGE_WS", "Mensagem processada com sucesso e enviada para o topico com nickname " + userNickname);
        }
    }

}