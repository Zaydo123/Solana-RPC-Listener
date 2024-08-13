package main

import (
	"context"
	"sync"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/redis/listeners"
	"github.com/rs/zerolog/log"
	//"github.com/Zaydo123/token-processor/internal/token/models"
)

func main() {

	wg := new(sync.WaitGroup)

	// ================== Load configuration ==================

	// Load configuration from environment variables
	findEnv := config.LoadEnv(5)

	if !findEnv {
		log.Fatal().Msg("Error loading environment variables. Exiting...")
		return
	}

	result := config.ParseEnv()

	if result == nil {
		log.Fatal().Msg("Error parsing environment variables. Exiting...")
		return
	}

	// ================== Start token processor ==================
	var ctx = context.Background()
	listeners.StartServices(ctx, wg)

}
