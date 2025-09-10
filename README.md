


# Telegive Giveaway Management Service

**A robust and scalable microservice for managing Telegram giveaways from creation to completion.**

This service provides a complete solution for creating, publishing, and managing giveaways on Telegram. It is designed to be part of a larger microservices architecture, interacting with other services for authentication, channel management, participant handling, and media storage.




## Features

* **Complete Giveaway Lifecycle Management:** Create, publish, and finish giveaways with a simple and intuitive API.
* **Single Active Giveaway Enforcement:** Prevent users from running multiple giveaways at the same time.
* **Inter-Service Communication:** Seamlessly integrates with other microservices for a complete solution.
* **Robust Error Handling:** Comprehensive error handling and validation to ensure data integrity.
* **Rate Limiting:** Protects the service from abuse and ensures fair usage.
* **Audit Logging:** Keeps a record of all important actions for security and compliance.
* **Health Checks:** Provides endpoints for monitoring the health and status of the service.
* **Comprehensive Testing:** Includes a full suite of unit, integration, and performance tests.
* **Containerized and Ready for Deployment:** Comes with a Dockerfile and deployment configurations for easy setup.




## Architecture Overview

This service is a central component of the Telegive ecosystem, responsible for orchestrating the giveaway process. It communicates with the following services:

* **Auth Service:** For user authentication and account validation.
* **Channel Service:** For managing Telegram channel permissions and settings.
* **Participant Service:** For handling giveaway participants and winner selection.
* **Bot Service:** For interacting with the Telegram Bot API to publish messages and send notifications.
* **Media Service:** For managing media files associated with giveaways.

This microservices architecture allows for a separation of concerns, making the system more scalable, maintainable, and resilient.




## API Documentation

### Endpoints

**Giveaways**

* `POST /api/giveaways/create`: Create a new giveaway.
* `GET /api/giveaways/active/{account_id}`: Get the active giveaway for an account.
* `POST /api/giveaways/{id}/publish`: Publish a giveaway to a Telegram channel.
* `PUT /api/giveaways/{id}/finish-messages`: Update the finish messages for a giveaway.
* `POST /api/giveaways/{id}/finish`: Finish a giveaway and select winners.
* `GET /api/giveaways/history/{account_id}`: Get the giveaway history for an account.
* `GET /api/giveaways/{id}/stats`: Get statistics for a giveaway.
* `GET /api/giveaways/by-token/{result_token}`: Get a giveaway by its result token.

**Health**

* `GET /health`: Get the health status of the service.

For detailed information on the API, please refer to the development specification document.




## Getting Started

### Prerequisites

* Docker
* Docker Compose

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/telegive-giveaway.git
   ```
2. Create a `.env` file from the `.env.example` and fill in the required environment variables.
3. Run the application using Docker Compose:
   ```bash
   docker-compose up --build
   ```

The service will be available at `http://localhost:8003`.




## Testing

To run the tests, use the following command:

```bash
pytest
```

This will run all the unit, integration, and performance tests and provide a coverage report.


