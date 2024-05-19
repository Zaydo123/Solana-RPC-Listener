# Solana Token Data Ingestor
| **Documentation** | **Build Status** | **Code Coverage** | **License** |
|:-----------------:|:----------------:|:-----------------:|:-----------:|
 |[![Documentation](https://img.shields.io/badge/docs-passing-brightgreen)](https://zaydo123.github.io/Solana-RPC-Listener/) | N/A | N/A | ![License](https://img.shields.io/badge/license-MIT-blue)|

## Description
This project, which is in progress, is a Solana RPC listener that listens for token transactions and stores, caches, and serves the data in a RESTful API. The ingested primarily focuses on token transactions and token mints, and will be used to power a trading bot that will be able to make trades based on the data it receives.

## Program Flow
[![Program Flow](./project_plan.png)](https://zaydo123.github.io/Solana-RPC-Listener/)

## Installation

### Clone the repository
```bash
git clone https://github.com/Zaydo123/Solana-RPC-Listener
```
### Change directory
```bash
cd Solana-RPC-Listener
```

### Install dependencies
```bash
pip install -r requirements.txt
```

### Environment Variables
Create a `.env` file in the root directory and add the following environment variables like so:
```bash
echo -e "DATABASE_URL=postgresql://user:password@localhost:5432/dbname
POSTGRES_DB = postgres
POSTGRES_USER = postgres
POSTGRES_PASSWORD = postgres" > .env
```

### Database Setup
Use the following commands to run the database in a docker container:
```bash 
docker compose up -d
```
make env file in prisma folder like so:
```bash
echo "DATABASE_URL=postgresql://user:password@localhost:5432/dbname" > prisma/.env
```
and then run the following commands to create the database tables and generate the prisma client:
```bash
cd prisma
prisma generate
prisma migrate dev --name init
```

Your database should now be set up and ready to go.

## Running the server (Note: The server is not yet fully functional)

### Development command
```bash
uvicorn main:app --reload --port 3000 --host 0.0.0.0
```

### Production command 
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app
```