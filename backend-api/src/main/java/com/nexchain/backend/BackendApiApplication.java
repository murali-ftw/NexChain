package com.nexchain.backend;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.event.ApplicationReadyEvent;
import org.springframework.context.ApplicationListener;
import org.springframework.context.event.ContextClosedEvent;
import org.springframework.stereotype.Component;

@SpringBootApplication
public class BackendApiApplication {

	private static final Logger log = LoggerFactory.getLogger(BackendApiApplication.class);

	public static void main(String[] args) {
		log.info("lifecycle event=starting service=backend-api");
		SpringApplication.run(BackendApiApplication.class, args);
	}

	/** Logs once dependency injection and startup have fully completed — the
	 * process is actually ready to serve traffic, not just that main() returned. */
	@Component
	static class ReadyLogger implements ApplicationListener<ApplicationReadyEvent> {
		@Override
		public void onApplicationEvent(ApplicationReadyEvent event) {
			log.info("lifecycle event=ready service=backend-api");
		}
	}

	/** Logs the start of graceful shutdown (SIGTERM, or the embedded server stopping),
	 * so an unexpected process exit is distinguishable from a normal one in the logs. */
	@Component
	static class ShutdownLogger implements ApplicationListener<ContextClosedEvent> {
		@Override
		public void onApplicationEvent(ContextClosedEvent event) {
			log.info("lifecycle event=shutting_down service=backend-api");
		}
	}

}
