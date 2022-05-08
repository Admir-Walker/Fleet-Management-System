# Fleet Management System

`Important note`: .env file is published for demo purposes only to ease application setup.

## Project structure
Project contains three services that are located in three separate folders.

- Fleet Management Service (FMS)
- GPS Simulator (GPS)
- Vehicle Monitoring System (VMS)


## Tech
Fleet Management System and its services use a number of open source projects to work properly:

- [FastAPI] - FastAPI is a modern, fast (high-performance), web framework for building APIs with Python 3.6+ based on standard Python type hints.
- [asyncio] - asyncio is a library to write concurrent code using the async/await syntax.
- [MongoDB] - MongoDB is an open source NoSQL database management program.
- [RabbitMQ] - RabbitMQ is the most widely deployed open source message broker.
- [Docker] - Docker is an open platform for developing, shipping, and running applications. 
- [Docker Compose] - Docker Compose is a tool for defining and running multi-container Docker applications. 


## Installation
### Installation using Docker

The easiest way to install, navigate to the project root and type in your preferred terminal:
```sh
$ docker-compose up -d
```

Verify the installation by navigating to link below in your preferred browser.

```sh
http://localhost:8008/docs
```

## Useful links
- Restful API Swagger documentation and playground: http://localhost:8008/docs
- Fleet Management Service database dashboard: http://localhost:8082/
- Vehicle Monitoring System database dashboard: http://localhost:8081/
- RabbitMQ dashboard: http://localhost:15672/

[FastAPI]: https://fastapi.tiangolo.com/
[asyncio]: https://docs.python.org/3/library/asyncio.html
[MongoDB]: https://www.mongodb.com/
[RabbitMQ]: https://www.rabbitmq.com/
[Docker]: https://www.docker.com/
[Docker Compose]: https://docs.docker.com/compose/
