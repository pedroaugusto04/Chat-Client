package com.pedro.sd.metrics;

import io.micrometer.core.instrument.MeterRegistry;
import io.micrometer.core.instrument.Timer;
import org.springframework.stereotype.Component;
import java.time.Duration;


@Component
public class MessageLatencyMetrics {

    private final Timer messageLatency;

    public MessageLatencyMetrics(MeterRegistry registry) {
        this.messageLatency = Timer.builder("message_latency_seconds")
                .description("Latencia do inicio do processamento ate a persistencia da mensagem no banco")
                .publishPercentileHistogram()
                .register(registry);
    }

    public void record(Duration latency) {
        messageLatency.record(latency);
    }
}
