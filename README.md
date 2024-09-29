<h1>Solana Token Data Ingestor</h1>

## Description
This project, which is in progress, is an G/RPC listener that listens for token transactions on the Raydium Constant Product AMM on the Solana Blockchain. The ingestor listens for swap transactions and mints along with burns if enabled. It continuously listens for these events and computes price, volume, and holdings changes; constantly caching then streaming the data via Kafka. From there, the data is then served through a RESTful API to trading and analytical microservices. The token data processing is done in golang for speed, the client API is built using FastAPI, and the G/RPC listener is in pure python. The database used is TimescaleDB and Interservice communication is done via Redis Pub/Sub and Kafka. All microservices along with Redis, Redis Commander, Kafka-UI, and TimescaleDB are currently being deployed using Docker Compose. It is recommended to host TimescaleDB, Kafka, and Redis on a cloud provider such as AWS, GCP, or Azure in production. For lowest latency, it is recommended to host the services in the same region/data center.

## Tech Stack
| Icon | Name | Description |
|---|---|---|
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width=50px /> | Python | For the G/RPC listener and API |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/fastapi/fastapi-original.svg" width=50px /> | FastAPI | Framework for the API |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/go/go-original.svg" width=50px /> | Go | For token data processing |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/redis/redis-original.svg" width=50px /> | Redis | For caching and pub/sub |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/apachekafka/apachekafka-original.svg" width=50px /> | Kafka | Persistence Queue | 
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/docker/docker-original.svg" width=50px /> | Docker | For containerization |
| <img src="./readme-assets/timescale.png" width=50px /> | TimescaleDB | Time series database for token data |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" width=50px />| ~~PostgreSQL~~ | ~~For persistent storage~~ (Migrated to TimescaleDB) |
| <img src="https://cdn.jsdelivr.net/gh/devicons/devicon@latest/icons/prisma/prisma-original.svg" /> | ~~Prisma~~ | ~~As the ORM~~ (Removed during migration) |

## Updated Program Flow Diagram
<img src="./final-wireframe.png" width=50% />


###  Bundled Services & Default Ports
- Redis :6379 Default
- Redis Commander :8080 Default
- Kafka :9092 Default
- Kafka-UI :8081 Default
- TimescaleDB :5432 Default



# SIMPLE INSTALLATION

### Clone the repository
```bash
git clone https://github.com/Zaydo123/Solana-RPC-Listener
```
### Go to the project directory
```bash
cd Solana-RPC-Listener
```
### Create Environment Variables
In each microservice directory, there should be a `.env.example` file. Copy the contents of the `.env.example` file and create a new `.env` file in the same directory. Fill in the values with your own.

### Build and Run the Docker Containers
```bash
docker-compose up --build
```

# MANUAL INSTALLATION

### Dependencies for the Python API and RPC Listener

In the microservice directory, run the following command to install the dependencies:
```bash
pip install -r requirements.txt
```
### Dependencies for the Go Token Data Processor
In the `token-data-processor` directory, run the following command to install the dependencies:
```bash
go mod tidy
go mod download
```

then you may build the binary using 
```bash
go build -tags musl -o myapp cmd/token-processor/main.go
````

### Production run command for Logger/API service
production run command
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app
```

development run command - configured with uvicorn
```bash
python main.py
```


# Common Issues
1. Pyscopg2 not installing on MacOS
   1. Install Homebrew
   2. Install openssl - `brew install openssl`
   3. If Processor >= M1 Chip:
      - `export LIBRARY_PATH=$LIBRARY_PATH:/opt/homebrew/opt/openssl/lib` - Adds openssl to the library path
    - Intel Macs:
      - `export LIBRARY_PATH=$LIBRARY_PATH:/usr/local/opt/openssl/lib/` - Adds openssl to the library path
   4. `pip install psycopg2`
2. Docker build failing on MacOS relating to confluent-kafka
   1. Instead of running barebones `go build`, run the following command:
      - `go build -tags musl -o myapp cmd/token-processor/main.go`
      - See more at https://github.com/confluentinc/confluent-kafka-go/issues/805

## Notes
- Events API / Logger is still in progress.
- Database automatically creates tables and columns on first run.
- Migration to TimescaleDB is in progress.
- The project is still in progress and is not yet complete.
- Trading services are not being shared in this repository.

