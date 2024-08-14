package models

import (
	bin "github.com/gagliardetto/binary"
	"github.com/gagliardetto/solana-go"
)

type LargestHolder struct {
	Holder string
	Amount float64
}

type LargestHolders struct {
	//list of largest holders
	Holders                []LargestHolder
	TopOwnershipPercentage float64
	Timestamp              int64 //date recorded
}

type TokenStandard bin.BorshEnum

type Key bin.BorshEnum

type UseMethod bin.BorshEnum

type Data struct {
	Name                 string
	Symbol               string
	URI                  string
	SellerFeeBasisPoints uint16
	Creators             *[]Creator `bin:"optional"`
}

type Creator struct {
	Address  solana.PublicKey
	Verified bool
	// In percentages, NOT basis points ;) Watch out!
	Share int8
}

type Collection struct {
	Verified bool
	Key      solana.PublicKey
}

type Uses struct {
	UseMethod UseMethod
	Remaining uint64
	Total     uint64
}

type Metadata struct {
	Key                 Key
	UpdateAuthority     solana.PublicKey
	Mint                solana.PublicKey
	Data                Data
	PrimarySaleHappened bool
	IsMutable           bool
	EditionNonce        *uint8         `bin:"optional"`
	TokenStandard       *TokenStandard `bin:"optional"`
	Collection          *Collection    `bin:"optional"`
	Uses                *Uses          `bin:"optional"`
}

type Token struct {
	ID              string
	PublicKey       solana.PublicKey
	PublicKeyString string
	Metadata        Metadata
	RealSupply      float64
	Supply          uint64
	Decimals        uint8
	Price           float64
	FreezeAuthority *solana.PublicKey `bin:"optional"`
	MintAuthority   *solana.PublicKey `bin:"optional"`
	Owner           string
	IsInitialized   bool
	InitialMint     int64 //date
	IPO             int64 //date
	LargestHolders  LargestHolders
	TotalBurned     int64
	LastUpdated     int64 //date
	LastCacheUpdate int64 //date
}
