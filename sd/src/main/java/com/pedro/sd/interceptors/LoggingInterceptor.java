package com.pedro.sd.interceptors;

import com.pedro.sd.services.LogsService;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.HandlerInterceptor;

@Component
public class LoggingInterceptor implements HandlerInterceptor {

    private final LogsService logsService;

    public LoggingInterceptor(LogsService logsService) {
        this.logsService = logsService;
    }

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {

        request.setAttribute("startTime", System.currentTimeMillis());

        logsService.log(null, "HTTP_REQUEST", "Entrou no endpoint " + request.getMethod() + " " + request.getRequestURI());

        return true;
    }

    @Override
    public void afterCompletion(HttpServletRequest request, HttpServletResponse response, Object handler, Exception ex) {

        long startTime = (long) request.getAttribute("startTime");
        long latency = System.currentTimeMillis() - startTime;

        String message = "Endpoint " + request.getMethod() + " " + request.getRequestURI() + " finalizado com status " + response.getStatus() + " em " + latency + " ms";

        logsService.log(null, "HTTP_RESPONSE", message);
    }
}

