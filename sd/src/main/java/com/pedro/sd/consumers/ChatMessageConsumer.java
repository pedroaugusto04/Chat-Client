package com.pedro.sd.consumers;

import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.DTO.ProcessedMessageDTO;
import com.pedro.sd.services.LogsService;
import com.pedro.sd.services.MessagesService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class ChatMessageConsumer {

    private final MessagesService messagesService;
    private final LogsService logsService;
    private final SimpMessagingTemplate messagingTemplate;

    public ChatMessageConsumer(MessagesService messagesService,
                               LogsService logsService,
                               SimpMessagingTemplate messagingTemplate) {
        this.messagesService = messagesService;
        this.logsService = logsService;
        this.messagingTemplate = messagingTemplate;
    }

    @KafkaListener(topics = "chat-messages", groupId = "chat-consumer-group")
    public void consume(ConsumerRecord<String, MessageSendDTO> messageRecord) {
        MessageSendDTO messageDTO = messageRecord.value();
        Integer groupId = Integer.valueOf(messageRecord.key());

        try {
            long startTime = System.currentTimeMillis();

            // persiste a mensagem no banco
            messagesService.sendMessage(groupId, messageDTO);

            long latency = System.currentTimeMillis() - startTime;

            logsService.log(messageDTO, "CONSUME_MESSAGE",
                    "Mensagem persistida no banco em " + latency + " ms");

            // envia a mensagem para os clientes ws conectados no grupo
            messagingTemplate.convertAndSend("/topic/messages." + groupId,
                    new MessageResponseDTO(
                            messageDTO.idemKey(),
                            messageDTO.text(),
                            null,
                            messageDTO.userNickname(),
                            messageDTO.timestampClient(),
                            messageDTO.sentTime()));

            // confirma o processamento da mensagem
            String userNickname = messageDTO.userNickname();
            if (userNickname != null && !userNickname.isEmpty()) {
                messagingTemplate.convertAndSend("/topic/acks." + userNickname,
                        new ProcessedMessageDTO(messageDTO.idemKey()));
            }

        } catch (Exception e) {
            logsService.log(messageDTO, "RETRY_MESSAGE", "Falha ao processar mensagem. Mantem na fila para tentativa de reenvio.");
            throw e;
        }
    }
}
