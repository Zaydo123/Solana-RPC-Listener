FROM golang:1.22.7-alpine AS build

RUN apk update && apk add gcc g++ libc-dev librdkafka-dev pkgconf

WORKDIR /app

COPY go.mod go.sum ./

RUN go mod download

COPY . .

RUN go build -tags musl -o myapp cmd/token-processor/main.go

## Deploy
FROM alpine:latest

RUN apk update && apk add gcc g++ libc-dev librdkafka-dev pkgconf

COPY --from=build /app/myapp /

ENTRYPOINT ["/myapp"]
