package main

import (
	"context"
	"sync"
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/redis/listeners"
	parser "github.com/Zaydo123/token-processor/internal/token/pairs"
	"github.com/gagliardetto/solana-go/rpc"
	"github.com/rs/zerolog/log"
	//"github.com/Zaydo123/token-processor/internal/token/models"
)

func main() {

	wg := new(sync.WaitGroup)

	// ================== Load configuration ==================

	config.LoadEnv(5)
	config.ParseEnv()

	tp := parser.NewTokenParser()
	//time the function
	start := time.Now()
	_, err := tp.RunAll(context.TODO(), "A4Fc2pxtyhZs4SUqSf7SvDUVG6Av7sQkKfpjMM42YJar", rpc.CommitmentFinalized)
	end := time.Now()
	elapsed := end.Sub(start)
	log.Info().Msgf("Time taken to get all info: %s", elapsed)

	if err != nil {
		log.Error().Err(err).Msg("Failed to get token info")
		return
	}

	// ================== Start services ==================
	var ctx = context.Background()
	listeners.StartServices(ctx, wg)

}
