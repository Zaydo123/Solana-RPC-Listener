package config

import (
	"os"
	"strconv"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog/log"
)

type Config struct {
	// Configuration for the token processor
	// The configuration is loaded from environment variables
	RedisHost             string
	RedisPort             int
	RedisPassword         string
	CacheTimeoutSeconds   int
	StaleIfDeadForSeconds int
	CacheTTLMinutes       int
	BurnsChannel          string
	NewPairsChannel       string
	ParsedPairsChannel    string
	PricesChannel         string
	SwapsChannel          string
	RPCURL                string
	RPCRateLimitTime      int
	RPCRateLimitBurst     int
	PriceInterval         int
	PriceFollowTime       int
	OwnersFollowTime      int
	OwnersInterval        int
}

var ApplicationConfig Config

func LoadEnv(limit int) bool {
	// searches for a .env file in the current directory and all parent directories
	// limit is the maximum layers of parent directories to search

	//look for the .env file in parent directories
	found := false
	foundLayer := 1
	path := ".env"
	log.Debug().Msgf("Searching for .env file in %d layers", limit)
	for i := 0; i < limit; i++ {
		_, err := os.Stat(path)
		if err == nil {
			found = true
			foundLayer = i
			break
		} else {
			path = "../" + path
		}
	}

	if !found {
		log.Warn().Msg("No .env file found")
		return false
	} else {
		log.Info().Msgf("Found .env file in layer %d", foundLayer)
	}

	err := godotenv.Load(path)
	if err != nil {
		log.Fatal().Err(err).Msg("Error loading .env file")
		return false
	}

	log.Info().Msg("Loaded .env file")
	return true

}

func GetEnv(key string) string {
	// Get the value of an environment variable
	value, exists := os.LookupEnv(key)
	if !exists {
		log.Warn().Msgf("Environment variable %s not found", key)
		return ""
	}
	return value
}

func ParseEnv() *Config {
	//load up the struct with the configuration
	ApplicationConfig.RedisHost = GetEnv("REDIS_HOST")

	redisPort, err := strconv.Atoi(GetEnv("REDIS_PORT"))

	if err != nil {
		log.Fatal().Err(err).Msg("Error parsing REDIS_PORT")
		return nil
	}

	ApplicationConfig.RedisPort = redisPort

	ApplicationConfig.RedisPassword = GetEnv("REDIS_PASSWORD")
	ApplicationConfig.BurnsChannel = GetEnv("REDIS_BURNS_CHANNEL")
	ApplicationConfig.NewPairsChannel = GetEnv("REDIS_NEW_PAIRS_CHANNEL")
	ApplicationConfig.ParsedPairsChannel = GetEnv("REDIS_PARSED_PAIRS_CHANNEL")
	ApplicationConfig.PricesChannel = GetEnv("REDIS_PRICES_CHANNEL")
	ApplicationConfig.SwapsChannel = GetEnv("REDIS_SWAPS_CHANNEL")
	ApplicationConfig.RPCURL = GetEnv("HTTP_PROVIDER_MAIN")
	rateLimitTime, err1 := strconv.Atoi(GetEnv("PROVIDER_MAIN_RATE_LIMIT_TIME"))
	rateLimitBurst, err2 := strconv.Atoi(GetEnv("PROVIDER_MAIN_RATE_LIMIT_BURST"))
	priceInterval, err3 := strconv.Atoi(GetEnv("PRICE_INTERVAL"))
	priceFollowTime, err4 := strconv.Atoi(GetEnv("PRICE_FOLLOW_TIME"))
	ownersFollowTime, err5 := strconv.Atoi(GetEnv("OWNERS_FOLLOW_TIME"))
	ownersInterval, err6 := strconv.Atoi(GetEnv("OWNERS_INTERVAL"))
	cacheTimeoutSeconds, err7 := strconv.Atoi(GetEnv("CACHE_TIMEOUT_SECONDS"))
	staleIfDeadForSeconds, err8 := strconv.Atoi(GetEnv("STALE_IF_DEAD_FOR_SECONDS"))

	cacheTTLMinutes, err9 := strconv.Atoi(GetEnv("CACHE_TTL_MINUTES"))

	if err1 != nil {
		log.Fatal().Err(err).Msg("Error parsing PROVIDER_MAIN_RATE_LIMIT_TIME")
		return nil
	}

	if err2 != nil {
		log.Fatal().Err(err).Msg("Error parsing PROVIDER_MAIN_RATE_LIMIT_BURST")
		return nil
	}

	if err3 != nil {
		log.Fatal().Err(err).Msg("Error parsing PRICE_INTERVAL")
		return nil
	}

	if err4 != nil {
		log.Fatal().Err(err).Msg("Error parsing PRICE_FOLLOW_TIME")
		return nil
	}

	if err5 != nil {
		log.Fatal().Err(err).Msg("Error parsing OWNERS_FOLLOW_TIME")
		return nil
	}

	if err6 != nil {
		log.Fatal().Err(err).Msg("Error parsing OWNERS_INTERVAL")
		return nil
	}

	if err7 != nil {
		log.Fatal().Err(err).Msg("Error parsing CACHE_TIMEOUT_SECONDS")
		return nil
	}

	if err8 != nil {
		log.Fatal().Err(err).Msg("Error parsing STALE_IF_DEAD_FOR_SECONDS")
		return nil
	}

	if err9 != nil {
		log.Fatal().Err(err).Msg("Error parsing CACHE_TTL_MINUTES")
		return nil
	}

	ApplicationConfig.RPCRateLimitTime = rateLimitTime
	ApplicationConfig.RPCRateLimitBurst = rateLimitBurst

	ApplicationConfig.PriceInterval = priceInterval
	ApplicationConfig.PriceFollowTime = priceFollowTime

	ApplicationConfig.OwnersFollowTime = ownersFollowTime
	ApplicationConfig.OwnersInterval = ownersInterval

	ApplicationConfig.CacheTimeoutSeconds = cacheTimeoutSeconds
	ApplicationConfig.StaleIfDeadForSeconds = staleIfDeadForSeconds

	ApplicationConfig.CacheTTLMinutes = cacheTTLMinutes

	return &ApplicationConfig

}

func GetConfig() *Config {
	return &ApplicationConfig
}
