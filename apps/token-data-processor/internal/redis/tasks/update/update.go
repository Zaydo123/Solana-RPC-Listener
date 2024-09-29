package update

import (
	"time"

	"github.com/Zaydo123/token-processor/internal/config"
	kafkaManager "github.com/Zaydo123/token-processor/internal/kafka/client"
	clientManager "github.com/Zaydo123/token-processor/internal/redis/client"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

var rdb *redis.Client = clientManager.GetRedisClient()
var context = clientManager.GetRedisClientContext()

func SetTokenData(tokenPtr *models.Token) {
	tries := 0
	if rdb == nil {
		for {
			if rdb == nil {
				tries++
				rdb = clientManager.GetRedisClient()
				log.Info().Msg("Redis client is nil, trying to refetch from local client manager")

				if tries > 5 {
					log.Error().Msg("Failed to get redis client - max tries exceeded")
					return
				}

				time.Sleep(500 * time.Millisecond)
			} else {
				context = clientManager.GetRedisClientContext()
				log.Info().Msg("Redis client acquired")
				break
			}
		}
	}

	data, err := tokenPtr.MarshalBinary()
	if err != nil {
		log.Error().Msgf("Failed to marshal token: %s", err.Error())
		return
	}

	result := rdb.Set(context, tokenPtr.PublicKeyString, data, time.Minute*time.Duration(config.ApplicationConfig.CacheTTLMinutes))
	if result.Err() != nil {
		log.Error().Msg(result.Err().Error())
		return
	}
	tokenPtr.LastCacheUpdate = time.Now().UTC().UnixMilli()
}

func UpdateTask(tokenMap *map[string]*models.Token) {

	for {
		for key, token := range *tokenMap {
			if token.LastCacheUpdate == 0 {
				//if not cached / new
				SetTokenData(token)
			}
			if token.LastCacheUpdate+time.Duration(config.ApplicationConfig.CacheTimeoutSeconds).Milliseconds() < time.Now().UTC().UnixMilli() {
				//if not dead
				if time.Now().UTC().UnixMilli() < token.LastUpdated+(time.Second*time.Duration(config.ApplicationConfig.StaleIfDeadForSeconds)).Milliseconds() { //if stale but not dead
					SetTokenData(token)
				} else { //is dead
					//check not 0 because 0 means it was never cached
					if token.LastCacheUpdate != 0 {
						log.Info().Msgf("Token data for %s is dead. Removing from local store.", key)

						//send last volume to kafka
						lastVolume := token.GetMostRecentVolumeObject()
						if lastVolume != nil {
							kafkaManager.SendTokenVolumeToKafka(token.PublicKeyString, lastVolume)
						}
						//send last burn to kafka
						lastBurnPeriod := token.GetMostRecentBurnPeriod()
						if lastBurnPeriod != nil {
							kafkaManager.SendTokenBurnToKafka(token.PublicKeyString, lastBurnPeriod)
						}

						//send last token object to kafka - without volume, burn, price - just to update meta and Totalbuy/sell totalburn, etx
						kafkaManager.SendFinalUpdateToKafka(token)

						//delete from local store
						delete(*tokenMap, key)
					} else {
						log.Warn().Msgf("Token data for %s is dead. Not removing from local store because it was never cached.", key) //should never happen (hopefully)
					}
				}
			}
		}
		time.Sleep(1 * time.Second)
	}
}
