package consumerevents

import "encoding/json"

type NewPairEventData struct {
	EventType        string  `json:"event_type"`
	BaseToken        string  `json:"base_token"`
	QuoteToken       string  `json:"quote_token"`
	BasePoolAccount  string  `json:"base_pool_account"`
	QuotePoolAccount string  `json:"quote_pool_account"`
	BlockTime        float64 `json:"block_time"`
}

type NewPairEvent struct {
	EventType string           `json:"event_type"`
	Data      NewPairEventData `json:"data"`
}

type SwapEventData struct {
	TransactionSignature string  `json:"signature"`
	TokenAddress         string  `json:"token_address"`
	TransactionType      string  `json:"transaction_type"`
	Maker                string  `json:"maker"`
	AmountSolana         string  `json:"amount_sol"`
	FeeSolana            string  `json:"fee_sol"`
	BlockTime            float64 `json:"block_time"`
}

type SwapEvent struct {
	EventType string        `json:"event_type"`
	Data      SwapEventData `json:"data"`
}

// Custom unmarshalling for SwapEvent
func (e *SwapEvent) UnmarshalJSON(data []byte) error {
	// Define an alias to avoid recursion
	type Alias SwapEvent
	aux := &struct {
		Data struct {
			Transaction SwapEventData `json:"transaction"`
		} `json:"data"`
		*Alias
	}{
		Alias: (*Alias)(e),
	}

	// Unmarshal the JSON into the aux struct
	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}

	// Manually set the extracted transaction data to the SwapEvent's Data field
	e.Data = aux.Data.Transaction
	return nil
}

type BurnEventData struct {
	TokenAddress string  `json:"token"`
	Account      string  `json:"account"`
	Authority    string  `json:"authority"`
	TokenAmount  string  `json:"amount"`
	BlockTime    float64 `json:"block_time"`
}

type BurnEvent struct {
	EventType string        `json:"event_type"`
	Data      BurnEventData `json:"data"`
}
