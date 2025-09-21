package com.pedro.sd.config;

import org.springframework.util.backoff.BackOff;
import org.springframework.util.backoff.BackOffExecution;

import java.util.Random;

public class BackOffWithJitter implements BackOff {

    private final long initialInterval;
    private final double multiplier;
    private final long maxJitter;
    private final Random random = new Random();

    public BackOffWithJitter(long initialInterval, double multiplier, long maxJitter) {
        this.initialInterval = initialInterval;
        this.multiplier = multiplier;
        this.maxJitter = maxJitter;
    }

    @Override
    public BackOffExecution start() {
        return new BackOffExecution() {
            private long nextInterval = initialInterval;

            @Override
            public long nextBackOff() {
                long jitter = (long) (random.nextDouble() * maxJitter);
                long intervalWithJitter = nextInterval + jitter;

                nextInterval = (long) ((nextInterval * multiplier));
                return intervalWithJitter;
            }
        };
    }
}