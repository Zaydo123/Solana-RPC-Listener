package swaps

import (
	"strconv"
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	consumerevents "github.com/Zaydo123/token-processor/internal/redis/models"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/rs/zerolog/log"
)

func ProcessSwapEvent(token *models.Token, swapEvent consumerevents.SwapEvent) {

	// TODO:
	// Step 1: Get the swap event data
	var buyVolume float64 = 0
	var sellVolume float64 = 0
	var err1, err2 error
	mostRecentVolume := token.GetMostRecentVolumeObject()
	if swapEvent.Data.TransactionType == "Buy" {
		buyVolume, err1 = strconv.ParseFloat(swapEvent.Data.AmountSolana, 64)
	} else {
		sellVolume, err2 = strconv.ParseFloat(swapEvent.Data.AmountSolana, 64)
	}
	if err1 != nil || err2 != nil {
		//log error
		log.Error().Msg("Error parsing float64 from string")
		return
	}

	// Step 2: Update the token's volume data, but dont make a new period if the last period is still open

	// if there are no volume periods, or the last volume period is closed
	// then create a new volume period with the swap time as the start time
	if mostRecentVolume == nil || mostRecentVolume.Time+float64(config.ApplicationConfig.PriceInterval) <= float64(swapEvent.Data.BlockTime) {
		token.AddVolume(swapEvent.Data.BlockTime, buyVolume, sellVolume)
	} else {
		// if the last volume period is still open, update the volume data
		//add to respective buy/sell volume
		if swapEvent.Data.TransactionType == "Buy" {
			mostRecentVolume.BuyVolume += buyVolume
		} else {
			mostRecentVolume.SellVolume += sellVolume
		}
		mostRecentVolume.Volume = buyVolume + sellVolume

		log.Info().Msgf("Updated Volume: %f", token.TotalVolume.TotalVolume)

	}

	// Step 3: Update the token's last updated time
	// last updated now (even if blocktime is in past)
	// because used to determine if token is stale or not

	// TODO: REPLACE After Task 2 in queue
	// -> 	Add token.Update() function which caches token in redis if last update has been X amount of time determined by env
	token.LastUpdated = time.Now().Unix()

}
