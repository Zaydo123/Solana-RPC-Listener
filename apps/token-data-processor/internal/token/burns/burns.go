package burns

import (
	"encoding/csv"
	"os"
	"sync"
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	kafkaManager "github.com/Zaydo123/token-processor/internal/kafka/client"
	consumerevents "github.com/Zaydo123/token-processor/internal/redis/models"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/rs/zerolog/log"
	"github.com/shopspring/decimal"
)

// Map of blacklisted token addresses and their last hit timestamps
var blacklist = map[string]string{}

type UnknownToken struct {
	TokenAddress string
	HitCount     int
	Burns        []models.BurnPeriod
}

// Map of unknown tokens and their hit count
var unknownTokens = map[string]UnknownToken{}

// Mutex to handle concurrent access to maps
var mu sync.Mutex

// backupBlacklistToFile backs up the blacklist to a CSV file
func backupBlacklistToFile(filePath string) {
	file, err := os.Create(filePath)
	if err != nil {
		log.Error().Err(err).Msg("Error creating blacklist file")
		return
	}
	defer file.Close()

	writer := csv.NewWriter(file)
	defer writer.Flush()

	// Write the blacklist to the CSV file
	mu.Lock()
	defer mu.Unlock()
	for tokenAddress, lastHit := range blacklist {
		writer.Write([]string{tokenAddress, lastHit})
	}

	// log.Info().Msg("Blacklist backed up successfully")
}

// reloadBlacklistFromFile reloads the blacklist from a CSV file
func reloadBlacklistFromFile(filePath string) {
	file, err := os.Open(filePath)
	if err != nil {
		log.Error().Err(err).Msg("Error opening blacklist file... creating new blacklist file")
		_, err := os.Create(filePath)
		if err != nil {
			log.Error().Err(err).Msg("Error creating blacklist file")
		}
		return
	}
	defer file.Close()

	reader := csv.NewReader(file)
	mu.Lock()
	defer mu.Unlock()
	for {
		record, err := reader.Read()
		if err != nil {
			break
		}
		if len(record) < 2 {
			log.Warn().Msg("Invalid record in blacklist file")
			continue
		}
		blacklist[record[0]] = record[1]
	}

	if len(blacklist) == 0 {
		log.Warn().Msg("Blacklist is empty")
	}
}

// IsBlacklisted checks if a token is blacklisted
func IsBlacklisted(tokenAddress string) bool {
	mu.Lock()
	defer mu.Unlock()
	_, ok := blacklist[tokenAddress]
	return ok
}

// TrackUnknownToken increments the counter for unknown tokens
func TrackUnknownToken(burnEvent consumerevents.BurnEvent) {
	tokenAddress := burnEvent.Data.TokenAddress

	mu.Lock()
	defer mu.Unlock()
	hitCount := unknownTokens[tokenAddress].HitCount

	if hitCount == 0 {
		hitCount = 1
		//new burn period with the token amount and block time
		unknownTokens[tokenAddress] = UnknownToken{
			TokenAddress: tokenAddress,
			HitCount:     hitCount,
			Burns: []models.BurnPeriod{
				{
					StartTime:    int64(burnEvent.Data.BlockTime),
					AmountBurned: decimal.RequireFromString(burnEvent.Data.TokenAmount),
				},
			},
		}
	} else {
		hitCount++
		// if the last burn period is older than the interval, create a new burn period
		if unknownTokens[tokenAddress].Burns[len(unknownTokens[tokenAddress].Burns)-1].StartTime+int64(config.ApplicationConfig.PriceInterval) < int64(burnEvent.Data.BlockTime) {
			burns := unknownTokens[tokenAddress]
			//new burn period with the token amount and block time
			burns.Burns = append(burns.Burns, models.BurnPeriod{
				StartTime:    int64(burnEvent.Data.BlockTime),
				AmountBurned: decimal.RequireFromString(burnEvent.Data.TokenAmount),
			})
			//update the token in the map
			unknownTokens[tokenAddress] = burns
		} else {
			//add the token amount to the last burn period
			unknownTokens[tokenAddress].Burns[len(unknownTokens[tokenAddress].Burns)-1].AmountBurned = unknownTokens[tokenAddress].Burns[len(unknownTokens[tokenAddress].Burns)-1].AmountBurned.Add(decimal.RequireFromString(burnEvent.Data.TokenAmount))
		}
		//update the hit count
		unknownToken := unknownTokens[tokenAddress]
		unknownToken.HitCount = hitCount
		unknownTokens[tokenAddress] = unknownToken
	}
	//if the token has been seen 5 times and the first burn period is older than 5 minutes, blacklist the token
	if unknownTokens[tokenAddress].HitCount >= 5 && time.Now().UTC().Unix()-unknownTokens[tokenAddress].Burns[0].StartTime > 5*60 {
		// Add to blacklist
		blacklist[tokenAddress] = time.Now().UTC().Format(time.RFC3339)
		delete(unknownTokens, tokenAddress)
		log.Info().Msgf("Token %s has been blacklisted after 5 events", tokenAddress)
	}
	// else just wait for the next event. it will be cleaned up if it's inactive

}

// CleanupUnknownTokens clears tokens that haven't been seen in the last 5 minutes
func CleanupUnknownTokens() {
	mu.Lock()
	defer mu.Unlock()
	threshold := time.Now().UTC().Add(-5 * time.Minute)
	totalDeleted := 0
	for tokenAddress, lastHit := range blacklist {
		lastHitTime, _ := time.Parse(time.RFC3339, lastHit)
		if lastHitTime.Before(threshold) {
			delete(unknownTokens, tokenAddress)
			totalDeleted++
		}
	}
	log.Info().Msgf("Cleaned up %d unknown tokens", totalDeleted)
	totalDeleted = 0
}

// BlackListRefreshTask reloads the blacklist from the file every intervalSeconds seconds
func BlackListRefreshTask(filePath string, intervalSeconds int) {
	reloadBlacklistFromFile(filePath)
	ticker := time.NewTicker(time.Second * time.Duration(intervalSeconds))
	for range ticker.C {
		reloadBlacklistFromFile(filePath)
	}
}

// ScheduledBackupTask backs up the blacklist to a file at regular intervals
func ScheduledBackupTask(filePath string, intervalSeconds int) {
	ticker := time.NewTicker(time.Second * time.Duration(intervalSeconds))
	for range ticker.C {
		backupBlacklistToFile(filePath)
	}
}

// CleanupTask runs the cleanup for unknown tokens at regular intervals
func CleanupTask(intervalSeconds int) {
	ticker := time.NewTicker(time.Second * time.Duration(intervalSeconds))
	for range ticker.C {
		CleanupUnknownTokens()
	}
}

// matching task will be used to match the token object with its corresponding burn events because burns usually occur before the token is added to the DEX
func MatchingTask(matchCheckInterval int, tokenMap *map[string]*models.Token) {
	ticker := time.NewTicker(time.Second * time.Duration(matchCheckInterval))
	for range ticker.C {
		mu.Lock()
		// check all unknown tokens and see if they are in the token map
		for tokenAddress, unknownToken := range unknownTokens {
			if _, ok := (*tokenMap)[tokenAddress]; ok {
				log.Info().Msgf("Burns: Matched token %s with %d burn events", tokenAddress, len(unknownToken.Burns))
				// if the token is found in the token map, add the burn periods to the token
				token := (*tokenMap)[tokenAddress]
				for _, burn := range unknownToken.Burns {
					if token.GetMostRecentBurnPeriod() == nil {
						token.AddBurnPeriod(burn.AmountBurned, burn.StartTime)
					} else {
						if token.GetMostRecentBurnPeriod().StartTime+int64(config.ApplicationConfig.PriceInterval) < burn.StartTime {
							token.AddBurnPeriod(burn.AmountBurned, burn.StartTime)
						} else {
							token.AddToCurrentBurnPeriod(burn.AmountBurned)
						}
					}
				}
				// remove the token from the unknown tokens map
				delete(unknownTokens, tokenAddress)
			}
		}

		mu.Unlock()
	}
}

// ProcessBurnEvent processes a burn event for a token
func ProcessBurnEvent(burnEvent consumerevents.BurnEvent, tokenMap *map[string]*models.Token) {
	if IsBlacklisted(burnEvent.Data.TokenAddress) {
		log.Info().Msgf("Token is blacklisted: %s", burnEvent.Data.TokenAddress)
		mu.Lock()
		// Update the last hit timestamp in memory
		blacklist[burnEvent.Data.TokenAddress] = time.Now().UTC().Format(time.RFC3339)
		mu.Unlock()
		return
	}

	// Find the token in the token map
	token, ok := (*tokenMap)[burnEvent.Data.TokenAddress]
	if !ok {
		// log.Info().Msg("Burns: token not found in token map... starting to track")
		TrackUnknownToken(burnEvent)
		return
	}

	// Process the burn event logic for the token
	if token.GetMostRecentBurnPeriod() == nil {
		// if there are no burn periods, create a new burn period
		token.AddBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount), int64(burnEvent.Data.BlockTime))
	} else {
		// if the last burn period is older than the interval, create a new burn period
		if token.GetMostRecentBurnPeriod().StartTime+int64(config.ApplicationConfig.PriceInterval) < int64(burnEvent.Data.BlockTime) {

			// send the last burn event to the kafka topic
			kafkaManager.SendTokenBurnToKafka(token.PublicKeyString, token.GetMostRecentBurnPeriod())
			token.AddBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount), int64(burnEvent.Data.BlockTime))

		} else {
			token.AddToCurrentBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount))
		}
	}

}
