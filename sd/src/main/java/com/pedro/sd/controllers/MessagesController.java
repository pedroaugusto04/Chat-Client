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

@RestController
public class MessagesController {

    private MessagesService messagesService;

    MessagesController(MessagesService messagesService) {
        this.messagesService = messagesService;
    }

    @PostMapping("/groups/{id}/messages")
    public ResponseEntity<Void> sendMessage(@PathVariable("id") Integer groupId, @RequestBody MessageSendDTO messageDTO) {

        this.messagesService.sendMessage(groupId, messageDTO);

        return ResponseEntity.ok().build();
    }

    @GetMapping("groups/{id}/messages")
    public ResponseEntity<List<MessageResponseDTO>> getLastMessages(

            @PathVariable("id") Integer groupId,
            @RequestParam(value = "since", required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) Date since,
            @RequestParam(value = "limit", defaultValue = "10") Integer limit) {

        List<MessageResponseDTO> messages = messagesService.getMessages(groupId, since, limit);

        return ResponseEntity.ok(messages);
    }
}