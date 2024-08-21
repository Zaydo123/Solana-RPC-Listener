package models

import (
	bin "github.com/gagliardetto/binary"
	"github.com/gagliardetto/solana-go"
	"github.com/shopspring/decimal"
)

type LargestHolder struct {
	Holder string
	Amount float64
}

type LargestHolders struct {
	//list of largest holders
	Holders                []LargestHolder
	TopOwnershipPercentage float64
	Timestamp              float64 //date recorded
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

// struct for volumes that keeps markers of time and volume at that time.
// times are in unix time
type Volume struct {
	Volume     float64
	BuyVolume  float64
	SellVolume float64
	Time       float64
}

type TotalVolume struct {
	TotalVolume     float64
	TotalBuyVolume  float64
	TotalSellVolume float64
}

type Price struct {
	Price decimal.Decimal
	Time  float64
}

type Token struct {
	ID               string
	PublicKey        solana.PublicKey
	PublicKeyString  string
	Metadata         Metadata
	RealSupply       float64
	Supply           uint64
	Decimals         uint8
	Prices           []Price
	Volumes          []Volume // note: the volumes are inexact because transactions are not retroactively analyzed. only swaps after the token is detected are recorded
	TotalVolume      TotalVolume
	NumberOfBuys     uint64
	NumberOfSells    uint64
	FreezeAuthority  solana.PublicKey `bin:"optional"`
	MintAuthority    solana.PublicKey `bin:"optional"`
	BasePoolAccount  solana.PublicKey
	QuotePoolAccount solana.PublicKey
	Owner            string
	IsInitialized    bool
	IPO              float64 //date
	LargestHolders   []LargestHolders
	TotalBurned      int64
	LastUpdated      int64   //date
	LastCacheUpdate  float64 //date
}

// ============================ Accessors ============================

// ================== Price Access  ==================

// Get Most Recent Price - float64
func (t *Token) GetMostRecentPrice() decimal.Decimal {
	return t.Prices[len(t.Prices)-1].Price
}

// Get Most Recent Price Object (Price, Time)
func (t *Token) GetMostRecentPriceObject() *Price {
	return &t.Prices[len(t.Prices)-1]
}

// ================== Volume Access  ==================

// Get Most Recent Volume - float64
// Returns the most recent volume or -1 if there are no volumes
func (t *Token) GetMostRecentVolume() float64 {

	if len(t.Volumes) == 0 {
		return -1
	}

	return t.Volumes[len(t.Volumes)-1].Volume
}

// Get Most Recent Volume Object (Volume, Time)
// Returns the most recent volume object or nil if there are no volumes
func (t *Token) GetMostRecentVolumeObject() *Volume {
	lenV := len(t.Volumes)
	if lenV == 0 {
		return nil
	}
	return &t.Volumes[lenV-1]
}

// ================== Holder State Access  ==================

// Get Current Top Holders
func (t *Token) GetCurrentTopHolders() []LargestHolder {
	return t.LargestHolders[len(t.LargestHolders)-1].Holders
}

// Get Current Top Holder Ownership Percentage
func (t *Token) GetCurrentTopHolderOwnershipPercentage() float64 {
	return t.LargestHolders[len(t.LargestHolders)-1].TopOwnershipPercentage
}

// ================== Time States  ==================

// Get Price at Time
/*
Params:
	time: unix time
Returns:
	price (float64): price at the time
	found (bool): if the time was found
*/
func (t *Token) GetPriceAtTime(time float64) (decimal.Decimal, bool) {
	// its likely not going to find a time at the exact time so return the price of the most recent time before the time
	for i := len(t.Prices) - 1; i >= 0; i-- {
		if t.Prices[i].Time <= time {
			return t.Prices[i].Price, true
		}
	}
	zero := decimal.NewFromInt(0)
	return zero, false
}

// Get Volume at Time
/*
Params:
	time: unix time
Returns:
	volume (float64): volume at the time
	found (bool): if the time was found
*/
func (t *Token) GetVolumeAtTime(time float64) (float64, bool) {
	// its likely not going to find a time at the exact time so return the volume of the most recent time before the time
	for i := len(t.Volumes) - 1; i >= 0; i-- {
		if t.Volumes[i].Time <= time {
			return t.Volumes[i].Volume, true
		}
	}

	return 0, false
}

// Get Top Holder Ownership Percentage at Time
/*
Params:
	time: unix time
Returns:
	percentage (float64): top holder ownership percentage at the time
	found (bool): if the time was found
*/
func (t *Token) GetTopHolderOwnershipPercentageAtTime(time float64) (float64, bool) {
	// its likely not going to find a time at the exact time so return the ownership percentage of the most recent time before the time
	for i := len(t.LargestHolders) - 1; i >= 0; i-- {
		if t.LargestHolders[i].Timestamp <= time {
			return t.LargestHolders[i].TopOwnershipPercentage, true
		}
	}

	return 0, false
}

func (t *Token) GetTopHoldersAtTime(time float64) ([]LargestHolder, bool) {
	// its likely not going to find a time at the exact time so return the ownership percentage of the most recent time before the time
	for i := len(t.LargestHolders) - 1; i >= 0; i-- {
		if t.LargestHolders[i].Timestamp <= time {
			return t.LargestHolders[i].Holders, true
		}
	}

	return nil, false
}

// ================== Index States  ==================

// Get Price at Index
/*
Params:
	index: index of the price
Returns:
	price (float64): price at the index
	found (bool): if the index was found
*/
func (t *Token) GetPriceAtIndex(index int) (decimal.Decimal, bool) {
	if index < len(t.Prices) {
		return t.Prices[index].Price, true
	}
	zero := decimal.NewFromInt(0)
	return zero, false
}

// Get Volume at Index
/*
Params:
	index: index of the volume
Returns:
	volume (float64): volume at the index
	found (bool): if the index was found
*/
func (t *Token) GetVolumeAtIndex(index int) (float64, bool) {
	if index < len(t.Volumes) {
		return t.Volumes[index].Volume, true
	}
	return 0, false
}

// Get Top Holder Ownership Percentage at Index
/*
Params:
	index: index of the ownership percentage
Returns:
	percentage (float64): top holder ownership percentage at the index
	found (bool): if the index was found
*/
func (t *Token) GetTopHolderOwnershipPercentageAtIndex(index int) (float64, bool) {
	if index < len(t.LargestHolders) {
		return t.LargestHolders[index].TopOwnershipPercentage, true
	}
	return 0, false
}

func (t *Token) GetTopHoldersAtIndex(index int) ([]LargestHolder, bool) {
	if index < len(t.LargestHolders) {
		return t.LargestHolders[index].Holders, true
	}
	return nil, false
}

// ============================ Mutators ============================

// ================== Price Mutators  ==================
// Add Price
func (t *Token) AddPrice(price decimal.Decimal, time float64) {
	t.Prices = append(t.Prices, Price{
		Price: price,
		Time:  time,
	})
}

// ================== Volume Mutators  ==================
// AddVolume
/*
Description: Adds a volume to the token and updates the total volumes
Params:
	time: unix time in float64
	buyVolume: buy volume
	sellVolume: sell volume
*/
func (t *Token) AddVolume(time float64, buyVolume float64, sellVolume float64) {

	buyPlusSell := buyVolume + sellVolume

	t.Volumes = append(t.Volumes, Volume{
		Volume:     buyPlusSell, //volume only for volume period
		Time:       time,
		BuyVolume:  buyVolume,
		SellVolume: sellVolume,
	})

	//update total volume
	t.TotalVolume.TotalBuyVolume += buyVolume
	t.TotalVolume.TotalSellVolume += sellVolume
	t.TotalVolume.TotalVolume += buyPlusSell

}

// ================ Holder State Mutators  ===============
// Add Top Holder
func (t *Token) AddTopHolder(holders LargestHolders) {
	t.LargestHolders = append(t.LargestHolders, holders)
}
