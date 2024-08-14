package rpcclient

import (
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/gagliardetto/solana-go/rpc"
	"github.com/rs/zerolog/log"
	"golang.org/x/time/rate"
)

var client rpc.Client

func ConnectRPC() *rpc.Client {

	// Connects to the RPC server
	log.Info().Msgf("Connecting to RPC server at %s", config.ApplicationConfig.RPCURL)
	jClient := rpc.NewWithLimiter(config.ApplicationConfig.RPCURL, rate.Every(time.Duration(config.ApplicationConfig.RPCRateLimitTime)), config.ApplicationConfig.RPCRateLimitBurst)
	client := rpc.NewWithCustomRPCClient(jClient)

	if client == nil {
		log.Fatal().Msg("Failed to connect to RPC server")
	}

	return client
}

func GetRPCClient() *rpc.Client {
	return &client
}
