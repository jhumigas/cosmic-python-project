# Architecture Patterns with Python

This repository is a showcase of architectural patterns widely used in industrial projects.
We start from a simple e-commerce use case:  the business decides to implement an exciting new way of allocating stock, instead of just considering good available in the warehouse, we will treat the goods on ships as real stock and part of our inventory, just with slightly longer lead times. Fewer goods will appear to be out of stock, we’ll sell more, and the business can save money by keeping lower inventory in the domestic warehouse.

## Introduction

For that purpose: we start with a simple architecture with:

* domain model: contain the core model of our domain (with just order line and batches), here we define value objects and entities to structure the concepts we work with
* repository: this layer enables interaction with a storage, we also implement an ORM
* service layer: this is the part that orchestrates the steps when we have to perform an operation like allocate

Then to have the most consistent interactions with our database, we introduce

* unit of work: this help have an abstraction over atomic operations
* aggregates: evolution of our models so that we can have concurrent operation given a cluster of associated objects

We then evolve our application so that it becomes a message processor, easier to integrate in an architecture with microservices, we introduce

* Events: Broadcast by an actor to all interested listeners. Events capture facts
* Commands: ​Instructions sent by one part of a system to another. Commands capture intent
* Command-Query Responsability Segregation : Basically, we start from the insight that most users are not going to buy, but just see the product. In our application we need to separation read and write queries so we introduce a modul views only use to read our product

## Pre-requisities

Make sure you have:

* uv: Python package and project manager ([instructions](https://docs.astral.sh/uv/getting-started/installation/))
* [Docker](https://www.docker.com/get-started/) or a docker container manager (use [colima](https://github.com/abiosoft/colima#installation) for macOs)

## Setup local env

```sh
make start-dev
```

This will spin up dev environment in docker, and run locally a fast api, that connects to docker.
We run the `make all` command prior to start the FastAPI in development mode to have some test data to work with.
Head to `http://127.0.0.1:8000/docs` for the swagger documentation, and perform some tests.

You can stop the dev env with

```sh
make stop-dev
```

## Run tests

To run all tests, you can use:

```sh
make all
```

## Architecture

![Component Diagram](./doc/img/allocation_service_message_processor.png)

## Project structure

```text
.
├── docker-compose.yml
├── Dockerfile
├── Makefile       <-- Commands to build, test and run locally the project
├── pyproject.toml <--  Build onfiguration file used for build and packaging tools
├── README.md
├── src
│   └── allocation
│       ├── __init__.py
│       ├── entrypoints                 <-- Main script to run the application
│       │   ├── fast_app.py             <-- Entrypoint to run a REST API
│       │   └── redis_eventconsumer.py  <-- Entrypoint to run an event consumer
│       ├── service_layer               <-- Orchestration layer
│       │   ├── __init__.py
│       │   ├── handlers.py             <-- Set of handlers to process command and events
│       │   ├── messagebus.py           <-- Orchestrator class that process events, and commands then handle persistence
│       │   └── unit_of_work.py         <-- Manage context over atomic operation to the database
│       ├── adapters
│       │   ├── __init__.py
│       │   ├── email.py                <-- Email module to send emil when needed
│       │   ├── notifications.py        <-- Notification interface and classes used to produce notification when needed
│       │   ├── orm.py                  <-- Actual definition of database table and mappings to our objects
│       │   ├── redis_eventpublisher.py <-- Simple publisher to redis
│       │   └── repository.py           <-- Actual layer to handle persistence
│       ├── domain
│       │   ├── __init__.py
│       │   ├── commands.py             <-- Command definition
│       │   ├── events.py               <-- Event definition
│       │   └── model.py                <-- Model definition
│       ├── bootstrap.py                <-- Dependencies initialization and bootstrapping
│       ├── config.py
│       └── logger.py
├── tests
│   ├── __init__.py
│   ├── conftest.py
│   ├── e2e
│   ├── integration
│   └── unit
└── uv.lock
```

