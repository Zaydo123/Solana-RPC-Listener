package client

import (
	"context"
	"strconv"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/redis/go-redis/v9"
	"github.com/rs/zerolog/log"
)

var rdb *redis.Client // Redis client
var RedisClientContext context.Context

func InitRedisClient(redis_host string, redis_port int, redis_password string, ctx *context.Context) redis.Client {

	RedisClientContext = *ctx

	rdb = redis.NewClient(&redis.Options{
		Addr:     config.ApplicationConfig.RedisHost + ":" + strconv.Itoa(config.ApplicationConfig.RedisPort),
		Password: config.ApplicationConfig.RedisPassword,
		DB:       0, // use default DB
		Protocol: 3, // use Redis v3
	})

	log.Info().Msgf("Connecting to Redis at %s:%d", config.ApplicationConfig.RedisHost, config.ApplicationConfig.RedisPort)

	_, err := rdb.Ping(*ctx).Result() // Declare err variable
	if err != nil {
		log.Fatal().Err(err).Msg("Error connecting to Redis")
		return *rdb
	}

	log.Info().Msgf("Connected at %s:%d", config.ApplicationConfig.RedisHost, config.ApplicationConfig.RedisPort)

	return *rdb

}

func PingRedisClient(ctx *context.Context) string {
	resp, err := rdb.Ping(*ctx).Result()
	if err != nil {
		log.Error().Err(err).Msg("Error pinging Redis client")
		return ""
	}
	return resp
}

func CloseRedisClient() bool {
	err := rdb.Close()
	if err != nil {
		log.Error().Err(err).Msg("Error closing Redis client")
		return false
	}
	log.Info().Msg("Redis client closed")
	return true
}

func GetRedisClient() *redis.Client {
	return rdb
}

func GetRedisClientContext() context.Context {
	return RedisClientContext
}

func BroadcastMessage(channel string, message string) {
	err := rdb.Publish(RedisClientContext, channel, message).Err()
	if err != nil {
		log.Error().Err(err).Msg("Error broadcasting message")
	}
}
