package com.pedro.sd.consumers;

import com.pedro.sd.metrics.MessageLatencyMetrics;
import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.models.DTO.ProcessedMessageDTO;
import com.pedro.sd.services.LogsService;
import com.pedro.sd.services.MessagesService;
import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.springframework.dao.DataIntegrityViolationException;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.support.Acknowledgment;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.Duration;
import java.time.OffsetDateTime;
import java.time.ZoneOffset;

@Component
public class ChatMessageConsumer {

    private final MessagesService messagesService;
    private final LogsService logsService;
    private final SimpMessagingTemplate messagingTemplate;
    private final MessageLatencyMetrics messageLatencyMetrics;

    public ChatMessageConsumer(MessagesService messagesService,
                               LogsService logsService,
                               SimpMessagingTemplate messagingTemplate, MessageLatencyMetrics latencyMetrics) {
        this.messagesService = messagesService;
        this.logsService = logsService;
        this.messagingTemplate = messagingTemplate;
        this.messageLatencyMetrics = latencyMetrics;
    }

    @KafkaListener(topics = "chat-messages", groupId = "${spring.kafka.consumer.group-id}", id = "chat-messages-listener")
    @Transactional("kafkaTransactionManager")
    public void consume(ConsumerRecord<String, MessageSendDTO> messageRecord, Acknowledgment ack) {

        MessageSendDTO messageDTO = messageRecord.value();
        Integer groupId = Integer.valueOf(messageRecord.key());

        long startTime = System.currentTimeMillis();


        try {

            if ("warmup".equals(messageRecord.key()) || "warmup".equals(messageRecord.value().getText())) {
                ack.acknowledge();
                return;
            }

            saveMessage(groupId,messageDTO,startTime);
            messageDTO.setTimestampServer(OffsetDateTime.now(ZoneOffset.UTC));
            confirmMessageProcess(messageDTO,groupId);
            ack.acknowledge();

            saveMetricsMessageEndpoint(messageDTO);

        } catch(DataIntegrityViolationException ex) {
            // idempotencia -> mensagem ja processada nao eh persistida novamente
            this.logsService.log(messageDTO, "MESSAGE_ALREADY_PROCESSED", "Mensagem ja processada");
            messageDTO.setTimestampServer(OffsetDateTime.now(ZoneOffset.UTC));
            confirmMessageProcess(messageDTO,groupId);
            ack.acknowledge();

            saveMetricsMessageEndpoint(messageDTO);

        } catch(Exception ex){
            this.logsService.log(messageDTO, "ERROR", "Erro ao salvar mensagem no banco " + ex.getMessage());
            throw ex;
        }
    }

    @Transactional
    public void saveMessage(Integer groupId, MessageSendDTO messageDTO,long startTime) {

        // persiste a mensagem no banco
        messagesService.sendMessage(groupId, messageDTO);

        long latency = System.currentTimeMillis() - startTime;

        logsService.log(messageDTO, "CONSUME_MESSAGE",
                "Mensagem persistida no banco em " + latency + " ms");
    }

    public void confirmMessageProcess(MessageSendDTO messageDTO, Integer groupId) {
        // envia a mensagem para os clientes ws conectados no grupo
        messagingTemplate.convertAndSend("/topic/messages." + groupId,
                new MessageResponseDTO(
                        messageDTO.getIdemKey(),
                        messageDTO.getText(),
                        null,
                        messageDTO.getUserNickname(),
                        messageDTO.getTimestampClient(),
                        messageDTO.getTimestampServer()));

        // confirma o processamento da mensagem
        String userNickname = messageDTO.getUserNickname();
        if (userNickname != null && !userNickname.isEmpty()) {
            messagingTemplate.convertAndSend("/topic/acks." + userNickname,
                    new ProcessedMessageDTO(messageDTO.getIdemKey()));
        }
    }

    public void saveMetricsMessageEndpoint(MessageSendDTO messageDTO) {
        if (messageDTO.getTimestampClient() != null) {
            Duration latency = Duration.between(
                    messageDTO.getTimestampClient(),
                    messageDTO.getTimestampServer()
            );
            messageLatencyMetrics.record(latency);
        }
    }
}