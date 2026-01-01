# Chat-Client

Desktop chat application with a backend server. The system was designed to be scalable, distributed, and robust, supporting multiple simultaneous clients while ensuring message delivery and deduplication.


## Functional Requirements

- Create and manage chat rooms/groups.

- Post messages in groups

- Read messages from all joined groups.

- Idempotency in message posting, preventing duplicates.

## Non-Functional Requirements

- Latency P95 ≤ 150 ms in a local network.
- Throughput > 100 messages/min.
- Server availability ≥ 99%.
- Generate logs for requests, errors, and latency.

## Architecture

**Server:**  
- Application server with **PostgreSQL** for persistent storage
- Designed for **distributed scalability** with **Nginx** (load balancing), **WebSockets** (low-latency-messaging), and **Apache Kafka** (message streaming)  
- Ensures **idempotency** using client-provided `idemKey`  

**Client:**  
- Desktop app (Python)  
  - `POST /nick {name}` – set nickname  
  - `POST /groups {name}` – create group  
  - `GET /groups` – list groups  
  - `POST /groups/{id}/messages {idemKey, text, timestamp_client}` – post message  
  - `GET /groups/{id}/messages?since=[cursor]&limit=10` – fetch messages
  - **Retry mechanism** for message posting with **backoff + jitter**.  

## Fault Tolerance & Scalability

- Clients **retry messages with backoff + jitter** until confirmation  
- Clients disconnect after inactivity; missed messages are available on reconnection.
- Horizontal scaling supported with multiple servers behind **Nginx**  
- Kafka ensures **durable message streaming**  
