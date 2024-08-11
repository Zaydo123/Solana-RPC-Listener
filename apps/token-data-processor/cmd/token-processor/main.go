package main

import (
	"context"
	"fmt"
	"os"
	"strconv"

	"github.com/Zaydo123/token-processor/internal/env"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

type Config struct {
	// Configuration for the token processor
	// The configuration is loaded from environment variables
	redis_host     string
	redis_port     int
	redis_password string
	burns_channel  string
}

var rdb *redis.Client // Redis client
var currentConfig Config

func main() {
	// Load configuration from environment variables
	result := env.LoadEnv(5)

	if !result {
		log.Fatal().Msg("Quitting")
		return
	}

	//load up the configuration
	redisHost := os.Getenv("REDIS_HOST")
	redisPort, err := strconv.Atoi(os.Getenv("REDIS_PORT"))
	redisPassword := os.Getenv("REDIS_PASSWORD")
	burnsChannel := os.Getenv("REDIS_BURNS_CHANNEL")

	if err != nil {
		log.Fatal().Err(err).Msg("Error parsing REDIS_PORT")
		return
	}

	if redisPassword == "" {
		log.Warn().Msg("REDIS_PASSWORD is empty")
	}

	if redisHost == "" {
		log.Fatal().Msg("REDIS_HOST is empty. Quitting")
		return
	}

	if redisPort == 0 {
		log.Fatal().Msg("REDIS_PORT is 0. Quitting")
		return
	}

	if burnsChannel == "" {
		log.Fatal().Msg("BURNS_CHANNEL is empty. Quitting")
		return
	}

	currentConfig = Config{
		redis_host:     redisHost,
		redis_port:     redisPort,
		redis_password: redisPassword,
		burns_channel:  burnsChannel,
	}

	log.Info().Msg("Starting token processor")

	// Start the token processor

	//connect to redis which is necessary for data ingestion
	var ctx = context.Background()
	rdb = redis.NewClient(&redis.Options{
		Addr:     currentConfig.redis_host + ":" + strconv.Itoa(currentConfig.redis_port),
		Password: currentConfig.redis_password,
		DB:       0, // use default DB
		Protocol: 3, // use Redis v3
	})

	_, err = rdb.Ping(ctx).Result()
	if err != nil {
		log.Fatal().Err(err).Msg("Error connecting to Redis")
		return
	}
	log.Info().Msgf("Connected to Redis at %s:%d", currentConfig.redis_host, currentConfig.redis_port)
	log.Info().Msg("Subscribing to burns channel")
	pubsub := rdb.Subscribe(ctx, currentConfig.burns_channel)

	for {
		msg, err := pubsub.ReceiveMessage(ctx)
		if err != nil {
			log.Err(err).Msg("Error receiving message")
			continue
		}
		fmt.Println(msg.Channel, msg.Payload)

	}

	//defer rdb.Close()

}
