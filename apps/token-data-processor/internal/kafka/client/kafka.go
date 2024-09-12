package client

import (
	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/confluentinc/confluent-kafka-go/kafka"
	"github.com/rs/zerolog/log"
)

var producer *kafka.Producer

// GetKafkaProducer initializes the Kafka producer with idempotent support
func GetKafkaProducer() *kafka.Producer {
	log.Info().Msgf("Connecting to Kafka broker at %s", config.ApplicationConfig.KafkaBroker)
	if producer == nil {
		p, err := kafka.NewProducer(&kafka.ConfigMap{
			"bootstrap.servers":  config.ApplicationConfig.KafkaBroker,
			"acks":               "all", // Wait for all replicas to acknowledge
			"enable.idempotence": true,  // Enable idempotent producer
			"retries":            5,     // Number of retries
			"retry.backoff.ms":   100,   // Retry backoff in milliseconds
		})
		if err != nil {
			panic(err)
		}
		producer = p
	}
	return producer
}

func SendTokenBasicDataToKafka(tokenObj *models.Token) {
	if producer == nil {
		producer = GetKafkaProducer()
	}
	marshaledToken, err := tokenObj.MarshalBinary()
	if err != nil {
		panic("Failed to marshal token: " + err.Error())
	}

	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.TokensTopic, Partition: kafka.PartitionAny},
		Value:          marshaledToken,
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // 15 seconds to flush
}

func SendTokenPriceToKafka(tokenAddressString string, priceObj *models.Price) {
	if producer == nil {
		producer = GetKafkaProducer()
	}

	// Marshal the price object
	marshaledPrice, err := priceObj.MarshalJSON()
	if err != nil {
		panic("Failed to marshal price: " + err.Error())
	}

	// Manually inject the tokenAddressString into the JSON
	// Convert marshaledPrice to a string, strip the final '}' and append the tokenAddress
	finalPriceJSON := string(marshaledPrice[:len(marshaledPrice)-1]) + `,"tokenAddress":"` + tokenAddressString + `"}`

	// Send the modified JSON to Kafka
	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.PricesTopic, Partition: kafka.PartitionAny},
		Value:          []byte(finalPriceJSON),
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // 15 seconds to flush
}

func SendTokenVolumeToKafka(tokenAddressString string, volumeObj *models.Volume) {
	if producer == nil {
		producer = GetKafkaProducer()
	}

	// Marshal the volume object
	marshaledVolume, err := volumeObj.MarshalJSON()
	if err != nil {
		panic("Failed to marshal volume: " + err.Error())
	}

	// Manually inject the tokenAddressString into the JSON
	// Convert marshaledVolume to a string, strip the final '}' and append the tokenAddress
	finalVolumeJSON := string(marshaledVolume[:len(marshaledVolume)-1]) + `,"tokenAddress":"` + tokenAddressString + `"}`

	// Send the modified JSON to Kafka
	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.VolumesTopic, Partition: kafka.PartitionAny},
		Value:          []byte(finalVolumeJSON),
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // 15 seconds to flush
}

func SendTopHoldersStateToKafka(tokenAddressString string, topHolders *models.LargestHolders) {
	if producer == nil {
		producer = GetKafkaProducer()
	}

	// Marshal the top holders object
	marshaledTopHolders, err := topHolders.MarshalJSON()
	if err != nil {
		panic("Failed to marshal top holders: " + err.Error())
	}

	// Manually inject the tokenAddressString into the JSON
	// Convert marshaledTopHolders to a string, strip the final '}' and append the tokenAddress
	finalTopHoldersJSON := string(marshaledTopHolders[:len(marshaledTopHolders)-1]) + `,"tokenAddress":"` + tokenAddressString + `"}`

	// Send the modified JSON to Kafka
	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.TopHoldersTopic, Partition: kafka.PartitionAny},
		Value:          []byte(finalTopHoldersJSON),
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // Wait for 15 seconds for messages to be sent
}

func SendTokenBurnToKafka(tokenAddressString string, burnObj *models.BurnPeriod) {
	if producer == nil {
		producer = GetKafkaProducer()
	}

	// Marshal the burn object
	marshaledBurn, err := burnObj.MarshalJSON()
	if err != nil {
		panic("Failed to marshal burn data: " + err.Error())
	}

	// Manually inject the tokenAddressString into the JSON
	// Convert marshaledBurn to a string, strip the final '}' and append the tokenAddress
	finalBurnJSON := string(marshaledBurn[:len(marshaledBurn)-1]) + `,"tokenAddress":"` + tokenAddressString + `"}`

	// Send the modified JSON to Kafka
	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.BurnsTopic, Partition: kafka.PartitionAny},
		Value:          []byte(finalBurnJSON),
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // Wait for 15 seconds for messages to be sent
}

// Sends the last necessary update to Kafka to ensure the token data is up-to-date
// It includes the token object with the latest data, excluding all time-series data: prices, volumes, burns, etc.
func SendFinalUpdateToKafka(tokenObj *models.Token) {
	if producer == nil {
		producer = GetKafkaProducer()
	}

	// remove all time-series data from the token object
	tokenObj.Prices = nil
	tokenObj.Volumes = nil
	tokenObj.BurnPeriods = nil
	tokenObj.LargestHolders = nil

	// Marshal the token object
	marshaledToken, err := tokenObj.MarshalBinary()
	if err != nil {
		panic("Failed to marshal token: " + err.Error())
	}

	// Send the token object to Kafka
	err = producer.Produce(&kafka.Message{
		TopicPartition: kafka.TopicPartition{Topic: &config.ApplicationConfig.TokensTopic, Partition: kafka.PartitionAny},
		Value:          marshaledToken,
	}, nil)

	if err != nil {
		log.Error().Msgf("Kafka send failed...")
	}

	// Optionally flush the producer to ensure delivery
	producer.Flush(15 * 1000) // Wait for 15 seconds for messages to be sent
}
