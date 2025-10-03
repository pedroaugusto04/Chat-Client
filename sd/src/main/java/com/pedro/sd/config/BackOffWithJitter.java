package com.pedro.sd.config;

import org.springframework.util.backoff.BackOff;
import org.springframework.util.backoff.BackOffExecution;

import java.util.Random;

public class BackOffWithJitter implements BackOff {

    private final long initialInterval;
    private final double multiplier;
    private final long maxJitter;
    private final int maxAttempts;
    private final Random random = new Random();

    public BackOffWithJitter(long initialInterval, double multiplier, long maxJitter, int maxAttempts) {
        this.initialInterval = initialInterval;
        this.multiplier = multiplier;
        this.maxJitter = maxJitter;
        this.maxAttempts = maxAttempts;
    }

    @Override
    public BackOffExecution start() {
        return new BackOffExecution() {
            private long nextInterval = initialInterval;
            private int attempt = 0;

            @Override
            public long nextBackOff() {
                if (attempt >= maxAttempts) {
                    return BackOffExecution.STOP;
                }
                attempt++;
                long jitter = (long) (random.nextDouble() * maxJitter);
                long intervalWithJitter = nextInterval + jitter;

                nextInterval = (long) ((nextInterval * multiplier));
                return intervalWithJitter;
            }
        };
    }
}