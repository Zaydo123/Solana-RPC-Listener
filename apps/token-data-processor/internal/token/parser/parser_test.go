package parser_test

import (
	"context"
	"fmt"
	"os"
	"testing"
	"time"

	"github.com/rs/zerolog/log"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/Zaydo123/token-processor/internal/token/parser"
	"github.com/gagliardetto/solana-go"
	"github.com/gagliardetto/solana-go/rpc"
)

func TestGetTokenInfoAndPrice(t *testing.T) {
	log.Logger = log.Output(os.Stdout) // Ensure logs are printed to stdout
	t.Log("Starting TestGetTokenInfoAndPrice")

	config.LoadEnv(7)
	config.ParseEnv()

	// Set up the context with a timeout
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Example Solana token public key (replace with a real one)
	pubkey := "Bn89xKUT7qyaJT6T64sjkRLuwNs1rQxVzaJADuDDeUBK"
	t.Logf("Using public key: %s", pubkey)

	// Optional: Set BasePoolAccount and QuotePoolAccount for price calculation
	basePoolPubKey := "5FmajWMXF3ANrs7g3wovgaCNtQ1gHqgs6ne2ca7j7JLi"
	quotePoolPubKey := "EhZLHCBBt5VDEDiAKkZdxQ9tVuBeLJ3oD9k7b9jVrn3t"

	basePoolAccount := solana.MustPublicKeyFromBase58(basePoolPubKey)
	quotePoolAccount := solana.MustPublicKeyFromBase58(quotePoolPubKey)

	// Initialize the TokenParser and fetch all token data, including price if pool accounts are provided
	tokenParser := parser.NewTokenParser()
	timeStart := time.Now()
	token, err := tokenParser.RunAll(ctx, pubkey, rpc.CommitmentFinalized, &basePoolAccount, &quotePoolAccount)
	timeEnd := time.Now()
	if err != nil {
		t.Fatalf("Failed to fetch token info: %v", err)
	}

	t.Logf("Token info fetched successfully in %v", timeEnd.Sub(timeStart))

	fmt.Printf("Token Price: %f\n", token.Price)
	// spew.Dump(token)
}

func TestGetTokenInfoWithoutPrice(t *testing.T) {
	log.Logger = log.Output(os.Stdout) // Ensure logs are printed to stdout
	t.Log("Starting TestGetTokenInfoWithoutPrice")

	config.LoadEnv(7)
	config.ParseEnv()

	// Set up the context with a timeout
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Example Solana token public key (replace with a real one)
	pubkey := "Bn89xKUT7qyaJT6T64sjkRLuwNs1rQxVzaJADuDDeUBK"
	t.Logf("Using public key: %s", pubkey)

	// Initialize the TokenParser and fetch all token data without price calculation
	tokenParser := parser.NewTokenParser()
	timeStart := time.Now()
	token, err := tokenParser.RunAll(ctx, pubkey, rpc.CommitmentFinalized, nil, nil)
	timeEnd := time.Now()
	if err != nil {
		t.Fatalf("Failed to fetch token info: %v", err)
	}

	t.Logf("Token info fetched successfully in %v", timeEnd.Sub(timeStart))

	fmt.Printf("Token Price: %f\n", token.Price)
	// spew.Dump(token)
}

func TestGetJustTokenPrice(t *testing.T) {
	log.Logger = log.Output(os.Stdout) // Ensure logs are printed to stdout
	t.Log("Starting TestGetJustTokenPrice")

	config.LoadEnv(7)
	config.ParseEnv()

	// Set up the context with a timeout
	ctx, cancel := context.WithTimeout(context.Background(), 60*time.Second)
	defer cancel()

	// Example Solana token public key (replace with a real one)
	pubkey := "Bn89xKUT7qyaJT6T64sjkRLuwNs1rQxVzaJADuDDeUBK"
	t.Logf("Using public key: %s", pubkey)

	// Set BasePoolAccount and QuotePoolAccount for price calculation
	basePoolPubKey := "5FmajWMXF3ANrs7g3wovgaCNtQ1gHqgs6ne2ca7j7JLi"
	quotePoolPubKey := "EhZLHCBBt5VDEDiAKkZdxQ9tVuBeLJ3oD9k7b9jVrn3t"

	basePoolAccount := solana.MustPublicKeyFromBase58(basePoolPubKey)
	quotePoolAccount := solana.MustPublicKeyFromBase58(quotePoolPubKey)

	// Initialize the TokenParser
	tokenParser := parser.NewTokenParser()

	// Fetch the price of the token using the provided pool accounts
	timeStart := time.Now()
	price := tokenParser.GetPrice(ctx, models.Token{
		BasePoolAccount:  basePoolAccount,
		QuotePoolAccount: quotePoolAccount,
	})
	timeEnd := time.Now()

	t.Logf("Token price fetched successfully in %v: %f", timeEnd.Sub(timeStart), price)
	if price == 0 {
		t.Fatalf("Failed to fetch token price or price is zero")
	}
}
