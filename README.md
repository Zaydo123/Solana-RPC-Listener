# Solana Webhook Listener
| **Documentation** | **Build Status** | **Code Coverage** | **License** |
|:-----------------:|:----------------:|:-----------------:|:-----------:|
 |[![Documentation](https://img.shields.io/badge/docs-passing-brightgreen)](https://zaydo123.github.io/Solana-RPC-Listener/) | N/A | N/A | ![License](https://img.shields.io/badge/license-MIT-blue)|

## Description
This is a solana transaction listener that listens to the solana rpc endpoint and stores the transactions in a database. The server is built using FastAPI and the database is managed using Prisma ORM. The purpose of this project is to provide a way to listen to solana transactions and store them in a database to later be used to train machine learning models. Once developed, the server will be able to listen to the solana rpc endpoint and store the transactions in a database with authenticated api endpoints to query the data.

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