package com.pedro.sd.config;

import com.pedro.sd.models.DTO.MessageSendDTO;
import com.pedro.sd.services.LogsService;
import org.apache.kafka.clients.admin.NewTopic;
import org.apache.kafka.clients.consumer.ConsumerConfig;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.common.serialization.StringDeserializer;
import org.apache.kafka.common.serialization.StringSerializer;
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

    // retry com backoff + jitter
    @Bean
    public ConcurrentKafkaListenerContainerFactory<String, MessageSendDTO> kafkaListenerContainerFactory() {
        ConcurrentKafkaListenerContainerFactory<String, MessageSendDTO> factory =
                new ConcurrentKafkaListenerContainerFactory<>();

        factory.setConsumerFactory(consumerFactory());
        factory.setConcurrency(5);
        factory.getContainerProperties().setAckMode(ContainerProperties.AckMode.MANUAL_IMMEDIATE);

        long initialInterval = 500;
        double multiplier = 2.0;
        long maxJitter = 500;

        BackOff backOff = new BackOffWithJitter(initialInterval, multiplier, maxJitter);

        DefaultErrorHandler errorHandler = new DefaultErrorHandler((record, exception) -> {
            logsService.log(record.value(), "RETRY_MESSAGE",
                    "Falha ao processar mensagem. Mantem na fila para uma nova tentativa de envio");
        }, backOff);

        factory.setCommonErrorHandler(errorHandler);
        return factory;
    }

    @Bean
    public KafkaTemplate<String, MessageSendDTO> kafkaTemplate() {
        return new KafkaTemplate<>(producerFactory());
    }

    @Bean
    public NewTopic topicChatMessages() {
        return TopicBuilder.name("chat-messages")
                .partitions(5)
                .replicas(1)
                .compact()
                .build();
    }
}
