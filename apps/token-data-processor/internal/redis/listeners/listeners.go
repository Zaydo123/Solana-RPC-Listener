package listeners

import (
	"context"
	"encoding/json"
	"sync"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/redis/client"
	ConsumerEvents "github.com/Zaydo123/token-processor/internal/redis/models"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

var rdb *redis.Client // Redis client

func receiveBurnMessages(ctx context.Context, wg *sync.WaitGroup) {
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

		//log.Info().Msgf("Received message: %s", msg.Payload)

		// Unmarshal the entire message directly into a BurnEvent
		var burnEvent ConsumerEvents.BurnEvent
		err = json.Unmarshal([]byte(msg.Payload), &burnEvent)
		if err != nil {
			log.Error().Err(err).Msg("Error parsing burn event")
			continue
		}

		// Log the fully populated BurnEvent, which includes the populated Data field
		log.Info().Msgf("Parsed BurnEvent: %+v", burnEvent)
		// TODO: Process the burn event further
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

		//log.Info().Msgf("Received message: %s", msg.Payload)

		// Parse the message into a NewPairEvent
		var newPairEvent ConsumerEvents.NewPairEvent
		err = json.Unmarshal([]byte(msg.Payload), &newPairEvent)
		if err != nil {
			log.Error().Err(err).Msg("Error parsing new pair event")
			continue
		}

		log.Info().Msgf("Parsed NewPairEvent: %+v", newPairEvent)
		// TODO: Process the new pair event further
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

		//log.Info().Msgf("Received message: %s", msg.Payload)

		// Unmarshal the entire message directly into a SwapEvent
		var swapEvent ConsumerEvents.SwapEvent
		err = json.Unmarshal([]byte(msg.Payload), &swapEvent)
		if err != nil {
			log.Error().Err(err).Msg("Error parsing swap event")
			continue
		}

		log.Info().Msgf("Parsed SwapEvent: %+v", swapEvent)
		// TODO: Process the swap event further
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
	go receiveBurnMessages(ctx, wg)

	// Receive new pairs messages
	wg.Add(1)
	go receiveNewPairsMessages(ctx, wg)

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
