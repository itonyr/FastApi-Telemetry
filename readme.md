
# FastAPI with OpenTelemetry and Jaeger Tracing

This project demonstrates how to build a simple FastAPI application instrumented with OpenTelemetry and Jaeger for distributed tracing, while also using SQLAlchemy with PostgreSQL for database access. The app provides an API to interact with a PostgreSQL database and allows for distributed tracing using Jaeger.

## Features

- **FastAPI**: Python web framework for building APIs.
- **PostgreSQL**: A relational database to store posts.
- **OpenTelemetry**: Used for tracing the API and database calls.
- **Jaeger**: A distributed tracing system that collects and displays traces from the app.

## Prerequisites

- Docker Desktop (or Docker Engine) installed on your machine.
- Docker CLI set up and working.

## Getting Started

### Step 1: Run PostgreSQL Container via Docker CLI

Run the following command to start a PostgreSQL container using the credentials in the FastAPI app:

```bash
docker run --name my-postgres -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_DB=test -p 5432:5432 -d postgres
```

This command will:
- Start a PostgreSQL container named `my-postgres`.
- Set the PostgreSQL user to `postgres`, the password to `mysecretpassword`, and the database name to `test`.
- Expose the PostgreSQL container on port `5432`.

#### Initializing the Posts Database: 

- 1: Exec into the running PostgreSQL container
docker exec -it my-postgres bash

- 2: Authenticate into PostgreSQL using psql
psql -U postgres

- 3: Create a new database (e.g., named 'newdb')
CREATE DATABASE newdb;

- 4: Connect to the new database
\c newdb

- 5: Create a new table (matching the schema from the FastAPI app)
CREATE TABLE test_table (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP
);

- 6: Insert some example data into the table
INSERT INTO test_table (name, created_at) VALUES ('Test Post 1', NOW()), ('Test Post 2', NOW());

- 7: Verify the data was inserted
SELECT * FROM test_table;


### Step 2: Run Jaeger Container via Docker CLI

To collect traces, you need to run Jaeger. Use the following command to start a Jaeger container:

```bash
docker run -d --name jaeger   -e COLLECTOR_ZIPKIN_HTTP_PORT=9411   -p 5775:5775/udp   -p 6831:6831/udp   -p 6832:6832/udp   -p 5778:5778   -p 16686:16686   -p 14268:14268   -p 14250:14250   -p 9411:9411   jaegertracing/all-in-one:1.22
```

This command will:
- Start a Jaeger container.
- Expose the Jaeger UI on port `16686` and other ports required for tracing.

### Step 3: Run FastAPI Application

Once your PostgreSQL and Jaeger containers are running, you can run the FastAPI application. The app will connect to PostgreSQL and send tracing information to Jaeger.

1. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Start the FastAPI application:
   ```bash
   uvicorn main:app --reload
   ```

The API will be available at `http://127.0.0.1:8000` and Jaeger will be available at `http://localhost:16686`.

## API Endpoints

### `GET /`
Returns a welcome message.

### `GET /posts/{post_id}`
Fetches a post by its ID from the PostgreSQL database.

## Tracing

- The OpenTelemetry instrumentation captures traces of API requests and database queries.
- Traces are sent to Jaeger for visualization, allowing you to monitor request and query latencies, and track issues across services.

## Cleaning Up

To stop and remove the containers, use the following commands:

```bash
docker stop my-postgres jaeger
docker rm my-postgres jaeger
```

