package models

// TokenData represents the data of a token

type LargestHolders struct {
	Holder string
	Amount int64
}

type Token struct {
	ID                  string
	PublicKey           string
	MetaName            string
	MetaSymbol          string
	MetaTicker          string
	MetaChangeAuthority string
	Supply              int64
	Decimals            int8
	Price               float64
	FreezeAuthority     string
	MintAuthority       string
	Owner               string
	InitialMint         int64 //date
	LastUpdated         int64 //date
	IPO                 int64 //date
	LargestHolders      []LargestHolders
	RugPull             bool
	RugPullDate         int64 //date
	TotalBurned         int64
}

// TokenDataProcessor processes token data
