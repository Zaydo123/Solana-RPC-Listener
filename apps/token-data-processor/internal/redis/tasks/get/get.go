package get

import (
	"context"
	"time"

	"github.com/Zaydo123/token-processor/internal/redis/client"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/redis/go-redis/v9"
)

func GetTokenData(key string) (*models.Token, error) {
	redisCtx, cancel := context.WithDeadline(context.Background(), time.Now().Add(7*time.Second)) // 7 seconds deadline
	defer cancel()
	var rdb *redis.Client = client.SmartGetClient(&redisCtx)
	result := rdb.Get(redisCtx, key)
	if result.Err() != nil {
		return nil, result.Err()
	}
	var token models.Token
	err := token.UnmarshalBinary([]byte(result.Val()))
	if err != nil {
		return nil, err
	}
	return &token, nil
}
