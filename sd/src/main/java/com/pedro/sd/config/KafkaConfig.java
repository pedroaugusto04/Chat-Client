package com.pedro.sd.config;

import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.services.LogsService;
import org.apache.kafka.clients.admin.AdminClientConfig;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.boot.ApplicationRunner;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.kafka.config.ConcurrentKafkaListenerContainerFactory;
import org.springframework.kafka.config.TopicBuilder;
import org.springframework.kafka.core.*;
import org.springframework.kafka.listener.ContainerProperties;
import org.springframework.kafka.listener.DefaultErrorHandler;
import org.springframework.kafka.support.serializer.JsonDeserializer;
import org.springframework.kafka.support.serializer.JsonSerializer;
import org.springframework.kafka.transaction.KafkaTransactionManager;
import org.springframework.util.backoff.BackOff;

import java.util.HashMap;
import java.util.Map;

@Configuration
public class KafkaConfig {

    @Value(value = "${spring.kafka.bootstrap-servers}")
    private String bootstrapAddress;

    private final LogsService logsService;

    public KafkaConfig(LogsService logsService) {
        this.logsService = logsService;
    }

    @Bean
    public ProducerFactory<String, MessageSendDTO> producerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ProducerConfig.BOOTSTRAP_SERVERS_CONFIG, "127.0.0.1:9092");
        props.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, StringSerializer.class);
        props.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, JsonSerializer.class);
        props.put(ProducerConfig.RETRIES_CONFIG, 10);
        props.put(ProducerConfig.RETRY_BACKOFF_MS_CONFIG, 500);

        DefaultKafkaProducerFactory<String, MessageSendDTO> factory =
                new DefaultKafkaProducerFactory<>(props);

        // habilita transacao pra kafka + banco
        factory.setTransactionIdPrefix("tx-");
        return factory;
    }

    @Bean
    public ConsumerFactory<String, MessageSendDTO> consumerFactory() {
        Map<String, Object> props = new HashMap<>();
        props.put(ConsumerConfig.BOOTSTRAP_SERVERS_CONFIG, "127.0.0.1:9092");
        props.put(ConsumerConfig.GROUP_ID_CONFIG, "chat-consumer-group");
        props.put(ConsumerConfig.KEY_DESERIALIZER_CLASS_CONFIG, StringDeserializer.class);
        props.put(ConsumerConfig.VALUE_DESERIALIZER_CLASS_CONFIG, JsonDeserializer.class);
        props.put(JsonDeserializer.TRUSTED_PACKAGES, "*");
        return new DefaultKafkaConsumerFactory<>(props);
    }

    // transacao unica kafka + banco
    @Bean
    public KafkaTransactionManager<String, MessageSendDTO> kafkaTransactionManager(
            ProducerFactory<String, MessageSendDTO> producerFactory) {
        return new KafkaTransactionManager<>(producerFactory);
    }

    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, MessageSendDTO> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, MessageSendDTO> factory =
                new ConcurrentKafkaListenerContainerFactory<>();

        factory.setConsumerFactory(consumerFactory());
        factory.setConcurrency(5);
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);
        factory.setCommonErrorHandler(kafkaErrorHandler());
        return factory;
    }


    // retry com backoff + jitter
    @Bean
    public DefaultErrorHandler kafkaErrorHandler() {
        long initialInterval = 500;
        double multiplier = 2.0;
        long maxJitter = 500;

        BackOff backOff = new BackOffWithJitter(initialInterval, multiplier, maxJitter);

        DefaultErrorHandler handler = new DefaultErrorHandler(backOff);

        // registra cada tentativa de retry
        handler.setRetryListeners((record, ex, deliveryAttempt) -> {
            long nextInterval = calculateNextInterval(initialInterval, multiplier, maxJitter, deliveryAttempt);
            logsService.log(record.value(), "RETRY_ATTEMPT",
                    "Falha ao processar mensagem. Tentativa: " + deliveryAttempt +
                            ", Próxima mensagem: " + nextInterval +
                            ", Exception: " + ex.getMessage());
        });

        return handler;
    }

    private long calculateNextInterval(long initial, double multiplier, long maxJitter, int attempt) {
        double interval = initial * Math.pow(multiplier, attempt - 1);
        long jitter = (long) (Math.random() * maxJitter);
        return (long) interval + jitter;
    }

    @Bean
    public KafkaTemplate<String, MessageSendDTO> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    @Bean
    public KafkaAdmin kafkaAdmin() {
        Map<String, Object> configs = new HashMap<>();
        configs.put(AdminClientConfig.BOOTSTRAP_SERVERS_CONFIG, bootstrapAddress);
        return new KafkaAdmin(configs);
    }

    @Bean
    public NewTopic topicChatMessages() {
        return TopicBuilder.name("chat-messages")
                .partitions(5)
                .replicas(2)
                .compact()
                .build();
    }

    // warmup para evitar delay no envio da primeira mensagem
    @Bean
    public ApplicationRunner runner(KafkaTemplate<String, MessageSendDTO> template) {
        return args -> template.executeInTransaction(t -> {
            MessageSendDTO warmupMessage = new MessageSendDTO();
            warmupMessage.setText("warmup");
            try {
                t.send("chat-messages", "warmup", warmupMessage).get();
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
            return null;
        });
    }
}
