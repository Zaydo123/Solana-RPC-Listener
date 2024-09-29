package prices

import (
	"context"
	"time"

	kafkaManager "github.com/Zaydo123/token-processor/internal/kafka/client"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/Zaydo123/token-processor/internal/token/parser"
	"github.com/confluentinc/confluent-kafka-go/v2/kafka"
	"github.com/shopspring/decimal"
)

// Follow the price for a given time
// The followTime is the time in seconds to follow the price
// The interval is the time in seconds to wait between each price fetch

var kafkaProducerClient *kafka.Producer

func FollowPrice(ctx context.Context, tokenParser *parser.TokenParser, tokenObj *models.Token, followTime int, interval int) {
	ticker := time.NewTicker(time.Duration(interval) * time.Second)
	var price decimal.Decimal
	defer ticker.Stop()

	// Follow the price for the given time
	for range ticker.C {
		followTime -= interval

		// Get the token price and add it to the token object
		price = tokenParser.GetPrice(ctx, *tokenObj)
		tokenObj.AddPrice(price, float64(time.Now().UTC().UnixMilli()))
		tokenObj.LastUpdated = time.Now().UTC().UnixMilli()

		// Send the token price to the kafka topic
		kafkaManager.SendTokenPriceToKafka(tokenObj.PublicKeyString, tokenObj.GetMostRecentPriceObject())

		// Check if the follow time has elapsed
		if followTime <= 0 {
			break
		}
	}

}
