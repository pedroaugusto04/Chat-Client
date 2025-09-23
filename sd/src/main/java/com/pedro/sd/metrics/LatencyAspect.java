package com.pedro.sd.metrics;


import com.pedro.sd.services.LogsService;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class LatencyAspect {

    private LogsService logsService;

    LatencyAspect(LogsService logsService){
        this.logsService = logsService;
    }

    @Around("execution(* com.pedro.sd.consumers.ChatMessageConsumer.consume(..))")
    public Object measureLatency(ProceedingJoinPoint joinPoint) throws Throwable {
        long start = System.currentTimeMillis();
        Object result = joinPoint.proceed();
        long latency = System.currentTimeMillis() - start;

        this.logsService.log(null,"LATENCIA","LATÊNCIA ENDPOINT sendMessageWS: " + latency + " ms");

        return result;
    }
}