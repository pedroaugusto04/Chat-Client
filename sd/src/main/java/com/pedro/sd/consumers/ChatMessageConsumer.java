package com.pedro.sd.consumers;

import com.pedro.sd.metrics.MessageLatencyMetrics;
import com.pedro.sd.models.DTO.MessageResponseDTO;
import com.pedro.sd.models.DTO.MessageSendDTO;
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
    public void consume(ConsumerRecord<String, MessageSendDTO> messageRecord, Acknowledgment ack) throws InterruptedException {

        MessageSendDTO messageDTO = messageRecord.value();

        long startTime = System.currentTimeMillis();


        try {

            if ("warmup".equals(messageRecord.key()) || "warmup".equals(messageRecord.value().getText())) {
                ack.acknowledge();
                return;
            }

            saveMessage(messageDTO,startTime);
            messageDTO.setTimestampEndServer(OffsetDateTime.now(ZoneOffset.UTC));
            confirmMessageProcess(messageDTO);
            ack.acknowledge();

            saveMetricsMessageEndpoint(messageDTO);

        } catch(DataIntegrityViolationException ex) {
            // idempotencia -> mensagem ja processada nao eh persistida novamente
            this.logsService.log(messageDTO, "MESSAGE_ALREADY_PROCESSED", "Mensagem ja processada");
            messageDTO.setTimestampEndServer(OffsetDateTime.now(ZoneOffset.UTC));
            confirmMessageProcess(messageDTO);
            ack.acknowledge();

            saveMetricsMessageEndpoint(messageDTO);

        } catch(Exception ex){
            this.logsService.log(messageDTO, "ERROR", "Erro ao salvar mensagem no banco " + ex.getMessage());
            throw ex;
        }
    }

    @Transactional
    public void saveMessage(MessageSendDTO messageDTO,long startTime) {

        // persiste a mensagem no banco
        messagesService.sendMessage(messageDTO);

        long latency = System.currentTimeMillis() - startTime;

        logsService.log(messageDTO, "CONSUME_MESSAGE",
                "Mensagem persistida no banco em " + latency + " ms");
    }

    public void confirmMessageProcess(MessageSendDTO messageDTO) {
        // envia a mensagem para os clientes ws conectados no grupo
        messagingTemplate.convertAndSend("/topic/messages." + messageDTO.getGroupId(),
                new MessageResponseDTO(
                        messageDTO.getIdemKey(),
                        messageDTO.getText(),
                        null,
                        messageDTO.getUserNickname(),
                        messageDTO.getTimestampClient()));
    }

    public void saveMetricsMessageEndpoint(MessageSendDTO messageDTO) {
        if (messageDTO.getTimestampClient() != null) {
            Duration latency = Duration.between(
                    messageDTO.getTimestampStartServer(),
                    messageDTO.getTimestampEndServer()
            );
            messageLatencyMetrics.record(latency);
        }
    }
}