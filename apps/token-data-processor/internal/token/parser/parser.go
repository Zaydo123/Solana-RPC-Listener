package parser

import (
	"context"
	"errors"
	"strconv"
	"strings"
	"sync"
	"time"

	rpcClientController "github.com/Zaydo123/token-processor/internal/rpc/client"
	"github.com/Zaydo123/token-processor/internal/token/models"
	bin "github.com/gagliardetto/binary"
	"github.com/gagliardetto/solana-go"
	"github.com/gagliardetto/solana-go/programs/token"
	"github.com/gagliardetto/solana-go/rpc"
	"github.com/rs/zerolog/log"
	"github.com/shopspring/decimal"
)

// TokenParser struct to manage methods related to token parsing
type TokenParser struct {
	client *rpc.Client
}

// NewTokenParser initializes a new TokenParser with an RPC client
func NewTokenParser() *TokenParser {
	client := rpcClientController.ConnectRPC()
	return &TokenParser{client: client}
}

// Utility function to trim null bytes from strings
func trimNullBytes(input string) string {
	return strings.TrimRight(input, "\x00")
}

var nullClient rpc.Client = rpc.Client{}

// GetPrice fetches the price of the token by comparing the base and quote pools.
func (tp *TokenParser) GetPrice(ctx context.Context, token models.Token) decimal.Decimal {

	zeroPrice := decimal.NewFromFloat(0.0)
	if *tp.client == nullClient || tp.client == nil {
		log.Error().Msg("RPC client is nil")
		return zeroPrice
	}

	if !tp.validateTokenPools(token) {
		return zeroPrice
	}

	basePoolAmt, quotePoolAmt := tp.fetchPoolBalancesConcurrently(ctx, token)
	if token.BasePoolAccount.IsZero() || token.QuotePoolAccount.IsZero() {
		log.Error().Msg("BasePoolAccount or QuotePoolAccount is not set (zero value)")
		return zeroPrice
	}

	if basePoolAmt == 0 || quotePoolAmt == 0 {
		return zeroPrice
	}

	price := tp.calculateTokenPrice(basePoolAmt, quotePoolAmt, token.Metadata.Data.Name)
	return price
}

// validateTokenPools checks if the BasePoolAccount and QuotePoolAccount are valid.
func (tp *TokenParser) validateTokenPools(token models.Token) bool {
	if token.BasePoolAccount.IsZero() || token.QuotePoolAccount.IsZero() {
		log.Error().Msg("BasePoolAccount or QuotePoolAccount is not set (zero value)")
		return false
	}

	// log.Info().Msgf("BasePoolAccount: %s, QuotePoolAccount: %s", token.BasePoolAccount.String(), token.QuotePoolAccount.String())
	return true
}

// fetchPoolBalancesConcurrently fetches the balances for the base and quote pools concurrently and returns them as floats.
func (tp *TokenParser) fetchPoolBalancesConcurrently(ctx context.Context, token models.Token) (basePoolAmt, quotePoolAmt float64) {

	if *tp.client == nullClient || tp.client == nil {
		log.Error().Msg("RPC client is nil")
		return 0, 0
	}

	var wg sync.WaitGroup
	wg.Add(2)

	basePoolChan := make(chan float64, 1)  // buffered channel with size 1
	quotePoolChan := make(chan float64, 1) // buffered channel with size 1

	// Fetch base pool account balance concurrently
	go func() {
		defer wg.Done()
		basePoolAmt := tp.fetchSinglePoolBalance(ctx, token.BasePoolAccount, "BasePoolAccount")
		basePoolChan <- basePoolAmt
	}()

	// Fetch quote pool account balance concurrently
	go func() {
		defer wg.Done()
		quotePoolAmt := tp.fetchSinglePoolBalance(ctx, token.QuotePoolAccount, "QuotePoolAccount")
		quotePoolChan <- quotePoolAmt
	}()

	// Wait for both goroutines to finish
	wg.Wait()
	close(basePoolChan)
	close(quotePoolChan)

	// Read the values from the channels
	basePoolAmt = <-basePoolChan
	quotePoolAmt = <-quotePoolChan

	return basePoolAmt, quotePoolAmt
}

// fetchSinglePoolBalance is a helper function to fetch the balance of a single pool account.
// It retries up to 3 times with exponential backoff if it fails.
func (tp *TokenParser) fetchSinglePoolBalance(ctx context.Context, poolAccount solana.PublicKey, accountType string) float64 {
	if *tp.client == nullClient || tp.client == nil {
		log.Error().Msg("RPC client is nil")
		return 0
	}

	const maxRetries = 3
	var attempt int
	var baseBackoff = time.Millisecond * 500 // initial backoff duration

	for attempt = 0; attempt < maxRetries; attempt++ {
		// log.Info().Msgf("Fetching %s balance for %s (Attempt %d)", accountType, poolAccount.String(), attempt+1)
		pool, err := tp.client.GetTokenAccountBalance(ctx, poolAccount, rpc.CommitmentProcessed)
		if err == nil && pool != nil {
			amount, parseErr := strconv.ParseFloat(pool.Value.UiAmountString, 64)
			if parseErr == nil {
				// log.Info().Msgf("Successfully fetched %s amount: %f", accountType, amount)
				return amount
			} else {
				log.Error().Err(parseErr).Msgf("Error parsing %s amount", accountType)
			}
		} else {
			log.Error().Err(err).Msgf("Failed to fetch %s balance on attempt %d", accountType, attempt+1)
		}

		// Exponential backoff before retrying
		time.Sleep(baseBackoff * (1 << attempt)) // increases wait time exponentially: 0.5s, 1s, 2s
	}

	log.Error().Msgf("All attempts to fetch %s balance failed", accountType)
	return 0
}

// calculateTokenPrice calculates the token price using the constant product formula and logs the result.
func (tp *TokenParser) calculateTokenPrice(basePoolAmt, quotePoolAmt float64, tokenName string) decimal.Decimal {
	price := decimal.NewFromFloat(quotePoolAmt).Div(decimal.NewFromFloat(basePoolAmt))
	return price
}

func (tp *TokenParser) GetMeta(ctx context.Context, pubKey solana.PublicKey) (*models.Metadata, error) {

	if *tp.client == nullClient || tp.client == nil {
		log.Error().Msg("RPC client is nil")
		return nil, errors.New("RPC client is nil")
	}

	tokenMetaAddr, numAddrs, err := solana.FindTokenMetadataAddress(pubKey)
	if err != nil {
		return nil, err
	} else if numAddrs == 0 {
		return nil, errors.New("no token metadata address found")
	}

	accountInfo, err := tp.client.GetAccountInfo(ctx, tokenMetaAddr)
	if err != nil {
		return nil, err
	}

	decodedData := accountInfo.Value.Data.GetBinary()
	var meta models.Metadata
	err = bin.NewBorshDecoder(decodedData).Decode(&meta)
	if err != nil {
		return nil, err
	}

	// Trim null bytes from the fields
	meta.Data.Name = trimNullBytes(meta.Data.Name)
	meta.Data.Symbol = trimNullBytes(meta.Data.Symbol)
	meta.Data.URI = trimNullBytes(meta.Data.URI)

	return &meta, nil
}

func (tp *TokenParser) GetInfo(ctx context.Context, pubkey string, commitment rpc.CommitmentType) (*models.Token, error) {

	if *tp.client == nullClient || tp.client == nil {
		log.Error().Msg("RPC client is nil")
		return nil, errors.New("RPC client is nil")
	}

	pubKey := solana.MustPublicKeyFromBase58(pubkey)
	resp, err := tp.client.GetAccountInfo(ctx, pubKey)
	if err != nil {
		return nil, err
	}

	var mint token.Mint
	var owner solana.PublicKey = resp.Value.Owner

	err = bin.NewBorshDecoder(resp.GetBinary()).Decode(&mint)
	if err != nil {
		return nil, err
	}

	// uint64 to string
	realSupplyStr := strconv.FormatUint(mint.Supply, 10)
	newStr := realSupplyStr[0:len(realSupplyStr)-int(mint.Decimals)] + "." + realSupplyStr[len(realSupplyStr)-int(mint.Decimals):]
	realSupply, err := strconv.ParseFloat(newStr, 64)
	if err != nil {
		return nil, err
	}

	currentToken := models.Token{
		PublicKey:       pubKey,
		PublicKeyString: pubkey,
		RealSupply:      realSupply,
		Supply:          mint.Supply,
		Decimals:        mint.Decimals,
		FreezeAuthority: solana.PublicKey{}, // default to empty if nil
		MintAuthority:   solana.PublicKey{}, // default to empty if nil
		IsInitialized:   mint.IsInitialized,
		LastUpdated:     time.Now().UnixMilli(),
		Owner:           owner.String(),
	}

	// Only assign if the pointer is not nil
	if mint.FreezeAuthority != nil {
		currentToken.FreezeAuthority = *mint.FreezeAuthority
	}
	if mint.MintAuthority != nil {
		currentToken.MintAuthority = *mint.MintAuthority
	}

	return &currentToken, nil
}

func (tp *TokenParser) GetLargestHolders(ctx context.Context, token *models.Token, commitment rpc.CommitmentType) (*models.LargestHolders, error) {
	largestAccountsReq, err := tp.client.GetTokenLargestAccounts(ctx, token.PublicKey, commitment)
	if err != nil {
		return nil, err
	}

	largestAccounts := largestAccountsReq.Value
	largestHolders := models.LargestHolders{
		Holders:   []models.LargestHolder{},
		Timestamp: float64(time.Now().UnixMilli()),
	}

	var sumOwned float64 = 0.0
	for _, account := range largestAccounts {

		realAmount, err := strconv.ParseFloat(account.UiAmountString, 64)
		if err != nil {
			return nil, err
		}
		sumOwned += realAmount
		holder := models.LargestHolder{
			Holder: account.Address.String(),
			Amount: realAmount,
		}
		largestHolders.Holders = append(largestHolders.Holders, holder)
	}

	topOwnershipPercentage := (sumOwned / token.RealSupply) * 100
	largestHolders.TopOwnershipPercentage = topOwnershipPercentage

	return &largestHolders, nil
}

// RunAll fetches all necessary data for the token, including price if BasePoolAccount and QuotePoolAccount are provided.
func (tp *TokenParser) RunAll(ctx context.Context, pubkey string, commitment rpc.CommitmentType, basePoolAccount, quotePoolAccount *solana.PublicKey) (*models.Token, error) {
	// log.Info().Msgf("Starting to fetch all data for token %s", pubkey)

	// Fetch Token Info first
	token, err := tp.GetInfo(ctx, pubkey, commitment)
	if err != nil {
		log.Error().Err(err).Msg("Error fetching token info")
		return nil, err
	}

	var wg sync.WaitGroup
	var meta *models.Metadata
	var holders *models.LargestHolders
	var price decimal.Decimal
	var metaErr, holdersErr error
	var mu sync.Mutex

	// Fetch Metadata and Largest Holders concurrently
	wg.Add(2)
	go func() {
		defer wg.Done()
		m, err := tp.GetMeta(ctx, token.PublicKey)
		mu.Lock()
		meta = m
		metaErr = err
		mu.Unlock()
	}()

	go func() {
		defer wg.Done()
		h, err := tp.GetLargestHolders(ctx, token, commitment)
		mu.Lock()
		holders = h
		holdersErr = err
		mu.Unlock()
	}()

	// Fetch Price if both BasePoolAccount and QuotePoolAccount are provided
	if basePoolAccount != nil && quotePoolAccount != nil {
		token.BasePoolAccount = *basePoolAccount
		token.QuotePoolAccount = *quotePoolAccount

		wg.Add(1)
		go func() {
			defer wg.Done()
			price = tp.GetPrice(ctx, *token)
		}()
	}

	// Wait for all goroutines to complete
	wg.Wait()

	// Check for errors
	if metaErr != nil {
		return nil, metaErr
	}
	if holdersErr != nil {
		return nil, holdersErr
	}

	// Assemble the final token object
	token.AddTopHolder(*holders)
	token.Metadata = *meta
	if basePoolAccount != nil && quotePoolAccount != nil {
		token.AddPrice(price, float64(time.Now().Unix())) // price isn't using block time, but current time
	}

	return token, nil
}
