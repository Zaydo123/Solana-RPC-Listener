package burns

import (
	"encoding/csv"
	"os"
	"sync"
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	consumerevents "github.com/Zaydo123/token-processor/internal/redis/models"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/rs/zerolog/log"
	"github.com/shopspring/decimal"
)

// Map of blacklisted token addresses and their last hit timestamps
var blacklist = map[string]string{}

// Map of unknown tokens and their hit count
var unknownTokens = map[string]int{}

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

	log.Info().Msg("Blacklist backed up successfully")
}

// reloadBlacklistFromFile reloads the blacklist from a CSV file
func reloadBlacklistFromFile(filePath string) {
	file, err := os.Open(filePath)
	if err != nil {
		log.Error().Err(err).Msg("Error opening blacklist file")
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
	} else {
		log.Info().Msg("Blacklist loaded successfully")
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
func TrackUnknownToken(tokenAddress string) {
	mu.Lock()
	defer mu.Unlock()
	unknownTokens[tokenAddress]++
	if unknownTokens[tokenAddress] > 4 {
		// Add to blacklist
		blacklist[tokenAddress] = time.Now().Format(time.RFC3339)
		delete(unknownTokens, tokenAddress)
		log.Info().Msgf("Token %s has been blacklisted after 5 events", tokenAddress)
	} else {
		log.Info().Msgf("Token %s has been seen %d times", tokenAddress, unknownTokens[tokenAddress])
	}

}

// CleanupUnknownTokens clears tokens that haven't been seen in the last 5 minutes
func CleanupUnknownTokens() {
	mu.Lock()
	defer mu.Unlock()
	threshold := time.Now().Add(-5 * time.Minute)
	for tokenAddress, lastHit := range blacklist {
		lastHitTime, _ := time.Parse(time.RFC3339, lastHit)
		if lastHitTime.Before(threshold) {
			delete(unknownTokens, tokenAddress)
			log.Info().Msgf("Token %s has been removed from unknown tokens list due to inactivity", tokenAddress)
		}
	}
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

// ProcessBurnEvent processes a burn event for a token
func ProcessBurnEvent(burnEvent consumerevents.BurnEvent, tokenMap *map[string]*models.Token) {
	log.Info().Msgf("Processing burn event for token: %s", burnEvent.Data.TokenAddress)

	if IsBlacklisted(burnEvent.Data.TokenAddress) {
		log.Info().Msgf("Token is blacklisted: %s", burnEvent.Data.TokenAddress)
		return
	}

	// Update the last hit timestamp in memory
	mu.Lock()
	blacklist[burnEvent.Data.TokenAddress] = time.Now().Format(time.RFC3339)
	mu.Unlock()

	// Find the token in the token map
	token, ok := (*tokenMap)[burnEvent.Data.TokenAddress]
	if !ok {
		log.Error().Msg("Token not found in token map")
		TrackUnknownToken(burnEvent.Data.TokenAddress)
		return
	}

	// Process the burn event logic for the token
	if token.GetMostRecentBurnPeriod() == nil {
		token.AddBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount), int64(burnEvent.Data.BlockTime))
	} else {
		if token.GetMostRecentBurnPeriod().StartTime+int64(config.ApplicationConfig.PriceInterval) < int64(burnEvent.Data.BlockTime) {
			token.AddBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount), int64(burnEvent.Data.BlockTime))
		} else {
			token.AddToCurrentBurnPeriod(decimal.RequireFromString(burnEvent.Data.TokenAmount))
		}
	}
}
