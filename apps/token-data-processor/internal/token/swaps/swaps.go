package swaps

import (
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	consumerevents "github.com/Zaydo123/token-processor/internal/redis/models"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/rs/zerolog/log"
	"github.com/shopspring/decimal"
)

func ProcessSwapEvent(token *models.Token, swapEvent consumerevents.SwapEvent) {

	// TODO:
	// Step 1: Get the swap event data
	buyVolume := decimal.NewFromFloat(0.0)
	sellVolume := decimal.NewFromFloat(0.0)
	var err1, err2 error
	mostRecentVolume := token.GetMostRecentVolumeObject()
	if swapEvent.Data.TransactionType == "Buy" {
		buyVolume, err1 = decimal.NewFromString(swapEvent.Data.AmountSolana)
	} else {
		sellVolume, err2 = decimal.NewFromString(swapEvent.Data.AmountSolana)
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
		//add to respective buy/sell counters
		if swapEvent.Data.TransactionType == "Buy" {
			token.NumberOfBuys++
		} else {
			token.NumberOfSells++
		}
		token.AddToCurrentVolumePeriod(buyVolume, sellVolume)

		log.Info().Msg("-----------------")
		log.Info().Msgf("Updated TV: %s | TBV %s | TSV %s", token.TotalVolume.TotalVolume.String(), token.TotalVolume.TotalBuyVolume.String(), token.TotalVolume.TotalSellVolume.String())
		log.Info().Msgf("CPV: %s | CBV: %s | CSV: %s", mostRecentVolume.Volume.String(), mostRecentVolume.BuyVolume.String(), mostRecentVolume.SellVolume.String())
		if sellVolume.GreaterThan(decimal.NewFromFloat(0.0)) {
			log.Info().Msgf("Buy: %s | Sell: %s | Ratio: %s", buyVolume.String(), sellVolume.String(), buyVolume.Div(sellVolume).String())
		}

	}

	// Step 3: Update the token's last updated time
	// last updated now (even if blocktime is in past)
	// because used to determine if token is stale or not

	// TODO: REPLACE After Task 2 in queue
	// -> 	Add token.Update() function which caches token in redis if last update has been X amount of time determined by env
	token.LastUpdated = time.Now().Unix()

}
