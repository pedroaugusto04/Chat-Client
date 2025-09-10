package com.pedro.sd.services;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Service;

@Service
public class LogsService {

    private static final Logger customLogger = LoggerFactory.getLogger("CUSTOM_LOGGER");

    public void log(Object object, String action, String message) {
        String objStr = object == null? "":object.toString();
        customLogger.info("OBJECT={} ACTION={} MESSAGE={} TIMESTAMP={}", objStr, action, message, System.currentTimeMillis());
    }
}


