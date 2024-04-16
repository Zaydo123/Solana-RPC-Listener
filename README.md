# Solana Webhook Listener
> in progress

### Description
This is a simple webhook server that listens for POST requests from the Solana RPC server. The server will act as a middleman between the Solana RPC server and the client. 

### Features
- [x] Listen for POST requests from the Solana RPC server
- [ ] Data Collection and Storage (PostgreSQL)
- [ ] Forward POST requests to the client

## Running the server

### Dev
```bash
uvicorn main:app --reload --port 3000 --host 0.0.0.0
```

### Prod
```bash
gunicorn -k uvicorn.workers.UvicornWorker main:app
```