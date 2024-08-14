package listeners

import (
	"context"
	"sync"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/redis/client"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

var rdb *redis.Client // Redis client

func receiveBurnsMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the burns channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, config.ApplicationConfig.BurnsChannel)

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
	pubsub := rdb.Subscribe(ctx, config.ApplicationConfig.NewPairsChannel)

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
	pubsub := rdb.Subscribe(ctx, config.ApplicationConfig.ParsedPairsChannel)

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
	pubsub := rdb.Subscribe(ctx, config.ApplicationConfig.PricesChannel)

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

func receiveSwapMessages(ctx context.Context, wg *sync.WaitGroup) {
	// Receive messages from the swaps channel
	defer wg.Done()
	pubsub := rdb.Subscribe(ctx, config.ApplicationConfig.SwapsChannel)

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

func StartServices(ctx context.Context, wg *sync.WaitGroup) {

	// Initialize the Redis client
	client.InitRedisClient(config.ApplicationConfig.RedisHost, config.ApplicationConfig.RedisPort, config.ApplicationConfig.RedisPassword, &ctx)
	rdb = client.GetRedisClient()

	// Start all the services
	log.Info().Msg("Starting services")

	// Receive burns messages
	wg.Add(1)
	go receiveBurnsMessages(ctx, wg)

	// Receive new pairs messages
	wg.Add(1)
	go receiveNewPairsMessages(ctx, wg)

	// Receive parsed pairs messages
	wg.Add(1)
	go receiveParsedPairsMessages(ctx, wg)

	// Receive prices messages
	wg.Add(1)
	go receivePricesMessages(ctx, wg)

	// Receive swaps messages
	wg.Add(1)
	go receiveSwapMessages(ctx, wg)

	log.Info().Msg("All services started")

	// Wait for all services to finish
	if wg != nil {
		wg.Wait()
	} else {
		log.Warn().Msg("Wait group is nil")
	}

	log.Info().Msg("All services stopped")
}
