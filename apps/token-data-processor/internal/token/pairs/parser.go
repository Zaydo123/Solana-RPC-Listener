package parser

import (
	"context"
	"errors"
	"log"
	"strconv"
	"strings"
	"sync"
	"time"

	rpcClient "github.com/Zaydo123/token-processor/internal/rpc/client"
	"github.com/Zaydo123/token-processor/internal/token/models"
	"github.com/davecgh/go-spew/spew"
	bin "github.com/gagliardetto/binary"
	"github.com/gagliardetto/solana-go"
	"github.com/gagliardetto/solana-go/programs/token"
	"github.com/gagliardetto/solana-go/rpc"
)

var client *rpc.Client

// trimNullBytes function remains as is because it's a utility function.
func trimNullBytes(input string) string {
	return strings.TrimRight(input, "\x00")
}

// TokenParser struct to manage methods related to token parsing
type TokenParser struct {
	client *rpc.Client
}

// NewTokenParser initializes a new TokenParser with an RPC client
func NewTokenParser() *TokenParser {
	if client == nil {
		client = rpcClient.ConnectRPC()
	}
	return &TokenParser{client: client}
}

func (tp *TokenParser) GetMeta(ctx context.Context, pubKey solana.PublicKey) (*models.Metadata, error) {
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

func (tp *TokenParser) GetInfo(pubkey string, commitment rpc.CommitmentType) (*models.Token, error) {
	pubKey := solana.MustPublicKeyFromBase58(pubkey)
	resp, err := tp.client.GetAccountInfo(context.TODO(), pubKey)
	if err != nil {
		panic(err)
	}

	var mint token.Mint
	var owner solana.PublicKey = resp.Value.Owner

	err = bin.NewBorshDecoder(resp.GetBinary()).Decode(&mint)
	if err != nil {
		panic(err)
	}

	//uint64 to string
	realSupplyStr := strconv.FormatUint(mint.Supply, 10)
	newStr := realSupplyStr[0:len(realSupplyStr)-int(mint.Decimals)] + "." + realSupplyStr[len(realSupplyStr)-int(mint.Decimals):]
	realSupply, err := strconv.ParseFloat(newStr, 64)

	if err != nil {
		return nil, err
	}

	currentToken := models.Token{
		PublicKey:       solana.MustPublicKeyFromBase58(pubkey),
		PublicKeyString: pubkey,
		RealSupply:      realSupply,
		Supply:          mint.Supply,
		Decimals:        mint.Decimals,
		FreezeAuthority: mint.FreezeAuthority,
		MintAuthority:   mint.MintAuthority,
		IsInitialized:   mint.IsInitialized,
		LastUpdated:     time.Now().Unix(),
		Owner:           owner.String(),
	}

	return &currentToken, nil
}

func (tp *TokenParser) GetLargestHolders(ctx context.Context, token *models.Token, commitment rpc.CommitmentType) error {
	largestAccountsReq, err := tp.client.GetTokenLargestAccounts(ctx, solana.MustPublicKeyFromBase58(token.PublicKeyString), commitment)
	if err != nil {
		return err
	}

	largestAccounts := largestAccountsReq.Value
	largestHolders := models.LargestHolders{
		Holders:   []models.LargestHolder{},
		Timestamp: time.Now().Unix(),
	}

	var sumOwned float64 = 0.0
	for _, account := range largestAccounts {

		realAmount, err := strconv.ParseFloat(account.UiAmountString, 64)
		if err != nil {
			return err
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

	token.LargestHolders = largestHolders
	return nil
}

// RunAll fetches token information, metadata, and largest holders simultaneously
func (tp *TokenParser) RunAll(ctx context.Context, pubkey string, commitment rpc.CommitmentType) (*models.Token, error) {
	var wg sync.WaitGroup
	var err error

	// Fetch Token Info (must be done first to get the basic token details)
	token, err := tp.GetInfo(pubkey, commitment)
	if err != nil {
		return nil, err
	}

	wg.Add(2) // Now we have two concurrent tasks (Meta and Largest Holders)

	// Fetch Metadata
	go func() {
		defer wg.Done()
		if token.PublicKeyString != "" {
			meta, metaErr := tp.GetMeta(ctx, token.PublicKey)
			if metaErr != nil {
				log.Printf("Error fetching metadata: %v", metaErr)
				err = metaErr
				return
			}
			token.Metadata = *meta
		}
	}()

	// Fetch Largest Holders
	go func() {
		defer wg.Done()
		if token.PublicKeyString != "" {
			largestHoldersErr := tp.GetLargestHolders(ctx, token, commitment)
			if largestHoldersErr != nil {
				log.Printf("Error fetching largest holders: %v", largestHoldersErr)
				err = largestHoldersErr
				return
			}
		}
	}()

	wg.Wait()

	// Return any errors encountered
	if err != nil {
		return nil, err
	}
	spew.Dump(token)
	return token, nil
}
