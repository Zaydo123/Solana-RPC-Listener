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

// struct for volumes that keeps markers of time and volume at that time.
// times are in unix time
type Volume struct {
	Volume float64
	Time   int64
}

type Price struct {
	Price float64
	Time  int64
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
	Volumes          []Volume
	FreezeAuthority  solana.PublicKey `bin:"optional"`
	MintAuthority    solana.PublicKey `bin:"optional"`
	BasePoolAccount  solana.PublicKey
	QuotePoolAccount solana.PublicKey
	Owner            string
	IsInitialized    bool
	IPO              int64 //date
	LargestHolders   []LargestHolders
	TotalBurned      int64
	LastUpdated      int64 //date
	LastCacheUpdate  int64 //date
}

// ============================ Accessors ============================

// ================== Price Access  ==================

// Get Most Recent Price - float64
func (t *Token) GetMostRecentPrice() float64 {
	return t.Prices[len(t.Prices)-1].Price
}

// Get Most Recent Price Object (Price, Time)
func (t *Token) GetMostRecentPriceObject() Price {
	return t.Prices[len(t.Prices)-1]
}

// ================== Volume Access  ==================

// Get Most Recent Volume - float64
func (t *Token) GetMostRecentVolume() float64 {
	return t.Volumes[len(t.Volumes)-1].Volume
}

// Get Most Recent Volume Object (Volume, Time)
func (t *Token) GetMostRecentVolumeObject() Volume {
	return t.Volumes[len(t.Volumes)-1]
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
func (t *Token) GetPriceAtTime(time int64) (float64, bool) {
	// its likely not going to find a time at the exact time so return the price of the most recent time before the time
	for i := len(t.Prices) - 1; i >= 0; i-- {
		if t.Prices[i].Time <= time {
			return t.Prices[i].Price, true
		}
	}

	return 0, false
}

// Get Volume at Time
/*
Params:
	time: unix time
Returns:
	volume (float64): volume at the time
	found (bool): if the time was found
*/
func (t *Token) GetVolumeAtTime(time int64) (float64, bool) {
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
func (t *Token) GetTopHolderOwnershipPercentageAtTime(time int64) (float64, bool) {
	// its likely not going to find a time at the exact time so return the ownership percentage of the most recent time before the time
	for i := len(t.LargestHolders) - 1; i >= 0; i-- {
		if t.LargestHolders[i].Timestamp <= time {
			return t.LargestHolders[i].TopOwnershipPercentage, true
		}
	}

	return 0, false
}

func (t *Token) GetTopHoldersAtTime(time int64) ([]LargestHolder, bool) {
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
func (t *Token) GetPriceAtIndex(index int) (float64, bool) {
	if index < len(t.Prices) {
		return t.Prices[index].Price, true
	}
	return 0, false
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
