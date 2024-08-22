package topownership

import (
	"context"
	"time"

	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/Zaydo123/token-processor/internal/token/parser"
	"github.com/gagliardetto/solana-go/rpc"
	"github.com/rs/zerolog/log"
)

func FollowTopOwnership(ctx context.Context, tokenParser *parser.TokenParser, tokenObj *models.Token, followTime int, interval int) {
	ticker := time.NewTicker(time.Duration(interval) * time.Second)
	defer ticker.Stop()

	// Follow the top ownership for the given time
	for range ticker.C {
		followTime -= interval
		// Get the token top ownership and add it to the token object
		topOwnership, err := tokenParser.GetLargestHolders(ctx, tokenObj, rpc.CommitmentProcessed)
		//float percentage print
		log.Info().Msgf("Top Ownership: %f | FRAME %d", topOwnership.TopOwnershipPercentage, len(tokenObj.LargestHolders))
		if err != nil {
			//log error
			log.Error().Msg("Error getting top ownership")
			return
		}

		tokenObj.AddTopHolder(*topOwnership) // Add state of top ownership to token object

		if followTime <= 0 {
			break
		}
	}

}
