package com.pedro.sd.controllers;

import java.util.Date;
import java.util.List;

import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.services.MessagesService;

import com.pedro.sd.services.LogsService;


@RestController
public class MessagesController {

    private MessagesService messagesService;
    private LogsService logsService;

    MessagesController(MessagesService messagesService, LogsService logsService) {
        this.messagesService = messagesService;
        this.logsService = logsService;
    }

    @PostMapping("/groups/{groupId}/messages")
    public ResponseEntity<Void> sendMessage(@PathVariable("groupId") Integer groupId, @RequestBody MessageSendDTO messageDTO) {

        this.logsService.log(messageDTO, "SEND_MESSAGE", "Entrou no endpoint para envio de mensagem");

        this.messagesService.sendMessage(groupId, messageDTO);

        this.logsService.log(messageDTO,"SEND_MESSAGE","Mensagem enviada com sucesso");

        return ResponseEntity.ok().build();
    }

    @GetMapping("groups/{id}/messages")
    public ResponseEntity<List<MessageResponseDTO>> getLastMessages(

            @PathVariable("id") Integer groupId,
            @RequestParam(value = "since", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date since,
            @RequestParam(value = "limit", defaultValue = "10") Integer limit) {

        this.logsService.log(groupId, "GET_MESSAGES", "Entrou no endpoint para recuperacao de mensagens do grupo");

        List<MessageResponseDTO> messages = messagesService.getMessages(groupId, since, limit);

        this.logsService.log(messages, "GET_MESSAGES", "Recuperou com sucesso as mensagens do grupo" + " " + groupId);

        return ResponseEntity.ok(messages);
    }
}