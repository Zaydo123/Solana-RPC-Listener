FROM golang:1.22.7-alpine AS build

RUN apk update && apk add gcc g++ libc-dev librdkafka-dev pkgconf

COPY . /app

WORKDIR /app

RUN go mod download

RUN go build -tags musl -o myapp cmd/token-processor/main.go

ENTRYPOINT ["/app/myapp"]
