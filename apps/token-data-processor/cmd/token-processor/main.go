package main

import (
	"context"
	"os"
	"strconv"
	"sync"

	"github.com/Zaydo123/token-processor/internal/env"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

type Config struct {
	// Configuration for the token processor
	// The configuration is loaded from environment variables
	redis_host           string
	redis_port           int
	redis_password       string
	burns_channel        string
	new_pairs_channel    string
	parsed_pairs_channel string
	REDIS_PRICES_CHANNEL string
}

var rdb *redis.Client // Redis client
var currentConfig Config

func receiveBurnsMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the burns channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, currentConfig.burns_channel)

	// Wait for messages
	for {
		msg, err := pubsub.ReceiveMessage(ctx)
		if err != nil {
			log.Error().Err(err).Msg("Error receiving message")
			return
		}

		log.Info().Msgf("Received message: %s", msg.Payload)
	}
}

func receiveNewPairsMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the new pairs channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, currentConfig.new_pairs_channel)

	// Wait for messages
	for {
		msg, err := pubsub.ReceiveMessage(ctx)
		if err != nil {
			log.Error().Err(err).Msg("Error receiving message")
			return
		}

		log.Info().Msgf("Received message: %s", msg.Payload)
	}
}

func receiveParsedPairsMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the parsed pairs channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, currentConfig.parsed_pairs_channel)

	// Wait for messages
	for {
		msg, err := pubsub.ReceiveMessage(ctx)
		if err != nil {
			log.Error().Err(err).Msg("Error receiving message")
			return
		}

		log.Info().Msgf("Received message: %s", msg.Payload)
	}
}

func receivePricesMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the prices channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, currentConfig.REDIS_PRICES_CHANNEL)

	// Wait for messages
	for {
		msg, err := pubsub.ReceiveMessage(ctx)
		if err != nil {
			log.Error().Err(err).Msg("Error receiving message")
			return
		}

		log.Info().Msgf("Received message: %s", msg.Payload)
	}
}

func main() {

	wg := new(sync.WaitGroup)

	// ================== Load configuration ==================

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
	newPairsChannel := os.Getenv("REDIS_NEW_PAIRS_CHANNEL")
	parsedPairsChannel := os.Getenv("REDIS_PARSED_PAIRS_CHANNEL")
	redisPricesChannel := os.Getenv("REDIS_PRICES_CHANNEL")

	if err != nil {
		log.Fatal().Err(err).Msg("Error parsing REDIS_PORT")
		return
	}

	// Check if any of the required environment variables are empty
	for _, envVar := range []string{"REDIS_PASSWORD", "REDIS_HOST", "REDIS_PORT", "REDIS_BURNS_CHANNEL", "REDIS_NEW_PAIRS_CHANNEL", "REDIS_PARSED_PAIRS_CHANNEL", "REDIS_PRICES_CHANNEL"} {
		if os.Getenv(envVar) == "" {
			log.Fatal().Msgf("Environment variable %s is empty", envVar)
			return
		}
	}

	// Create the configuration object
	currentConfig = Config{
		redis_host:           redisHost,
		redis_port:           redisPort,
		redis_password:       redisPassword,
		burns_channel:        burnsChannel,
		new_pairs_channel:    newPairsChannel,
		parsed_pairs_channel: parsedPairsChannel,
		REDIS_PRICES_CHANNEL: redisPricesChannel,
	}

	// ================== Start token processor ==================

	log.Info().Msg("Starting token processor")
	// Start the token processor

	//connect to redis which is necessary for data ingestion from other services
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

	// ------------------ Receive burns messages ------------------
	wg.Add(1)
	go receiveBurnsMessages(ctx, wg)
	log.Info().Msg("Burn processor started")

	// ------------------ Receive new pairs messages ------------------
	wg.Add(1)
	go receiveNewPairsMessages(ctx, wg)
	log.Info().Msg("New pairs processor started")

	// ------------------ Receive parsed pairs messages ------------------
	wg.Add(1)
	go receiveParsedPairsMessages(ctx, wg)
	log.Info().Msg("Parsed pairs processor started")

	// ------------------ Receive prices messages ------------------
	wg.Add(1)
	go receivePricesMessages(ctx, wg)
	log.Info().Msg("Prices processor started")

	log.Info().Msg("Token processor started successfully")

	// Wait forever
	wg.Wait()

}
