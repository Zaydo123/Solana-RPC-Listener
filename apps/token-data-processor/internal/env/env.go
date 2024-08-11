package env

import (
	"os"

	"github.com/joho/godotenv"
	"github.com/rs/zerolog/log"
)

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
