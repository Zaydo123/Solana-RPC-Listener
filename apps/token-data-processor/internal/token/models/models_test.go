package models

import (
	"testing"
	"time"
)

func TestToken_Accessors(t *testing.T) {
	now := time.Now().Unix()

	// Setup test data
	prices := []Price{
		{Price: 100.0, Time: now - 100},
		{Price: 105.0, Time: now - 50},
		{Price: 110.0, Time: now - 10},
	}

	volumes := []Volume{
		{Volume: 1000.0, Time: now - 100},
		{Volume: 1500.0, Time: now - 50},
		{Volume: 2000.0, Time: now - 10},
	}

	holders := []LargestHolders{
		{
			Holders:                []LargestHolder{{Holder: "holder1", Amount: 500}},
			TopOwnershipPercentage: 50.0,
			Timestamp:              now - 100,
		},
		{
			Holders:                []LargestHolder{{Holder: "holder2", Amount: 600}},
			TopOwnershipPercentage: 60.0,
			Timestamp:              now - 50,
		},
	}

	token := Token{
		Prices:         prices,
		Volumes:        volumes,
		LargestHolders: holders,
	}

	// Test GetMostRecentPrice
	expectedPrice := 110.0
	actualPrice := token.GetMostRecentPrice()
	if actualPrice != expectedPrice {
		t.Errorf("expected price %v, got %v", expectedPrice, actualPrice)
	}

	// Test GetMostRecentPriceObject
	expectedPriceObject := prices[2]
	actualPriceObject := token.GetMostRecentPriceObject()
	if actualPriceObject != expectedPriceObject {
		t.Errorf("expected price object %v, got %v", expectedPriceObject, actualPriceObject)
	}

	// Test GetMostRecentVolume
	expectedVolume := 2000.0
	actualVolume := token.GetMostRecentVolume()
	if actualVolume != expectedVolume {
		t.Errorf("expected volume %v, got %v", expectedVolume, actualVolume)
	}

	// Test GetMostRecentVolumeObject
	expectedVolumeObject := volumes[2]
	actualVolumeObject := token.GetMostRecentVolumeObject()
	if actualVolumeObject != expectedVolumeObject {
		t.Errorf("expected volume object %v, got %v", expectedVolumeObject, actualVolumeObject)
	}

	// Test GetCurrentTopHolders
	expectedHolders := holders[1].Holders
	actualHolders := token.GetCurrentTopHolders()
	if len(actualHolders) != len(expectedHolders) || actualHolders[0].Holder != expectedHolders[0].Holder {
		t.Errorf("expected holders %v, got %v", expectedHolders, actualHolders)
	}

	// Test GetCurrentTopHolderOwnershipPercentage
	expectedOwnershipPercentage := 60.0
	actualOwnershipPercentage := token.GetCurrentTopHolderOwnershipPercentage()
	if actualOwnershipPercentage != expectedOwnershipPercentage {
		t.Errorf("expected ownership percentage %v, got %v", expectedOwnershipPercentage, actualOwnershipPercentage)
	}

	// Test GetPriceAtTime - should return the price closest to and before the specified time
	expectedPriceAtTime := 105.0
	actualPriceAtTime, found := token.GetPriceAtTime(now - 55)
	if !found || actualPriceAtTime != expectedPriceAtTime {
		t.Errorf("expected price at time %v, got %v", expectedPriceAtTime, actualPriceAtTime)
	}

	// Test GetVolumeAtTime - should return the volume closest to and before the specified time
	expectedVolumeAtTime := 1500.0
	actualVolumeAtTime, found := token.GetVolumeAtTime(now - 55)
	if !found || actualVolumeAtTime != expectedVolumeAtTime {
		t.Errorf("expected volume at time %v, got %v", expectedVolumeAtTime, actualVolumeAtTime)
	}

	// Test GetTopHolderOwnershipPercentageAtTime
	expectedOwnershipAtTime := 50.0
	actualOwnershipAtTime, found := token.GetTopHolderOwnershipPercentageAtTime(now - 100)
	if !found || actualOwnershipAtTime != expectedOwnershipAtTime {
		t.Errorf("expected ownership at time %v, got %v", expectedOwnershipAtTime, actualOwnershipAtTime)
	}

	// Test GetTopHoldersAtTime
	expectedHoldersAtTime := holders[0].Holders
	actualHoldersAtTime, found := token.GetTopHoldersAtTime(now - 100)
	if !found || len(actualHoldersAtTime) != len(expectedHoldersAtTime) || actualHoldersAtTime[0].Holder != expectedHoldersAtTime[0].Holder {
		t.Errorf("expected holders at time %v, got %v", expectedHoldersAtTime, actualHoldersAtTime)
	}

	// Test GetPriceAtIndex
	expectedPriceAtIndex := 105.0
	actualPriceAtIndex, found := token.GetPriceAtIndex(1)
	if !found || actualPriceAtIndex != expectedPriceAtIndex {
		t.Errorf("expected price at index %v, got %v", expectedPriceAtIndex, actualPriceAtIndex)
	}

	// Test GetVolumeAtIndex
	expectedVolumeAtIndex := 1500.0
	actualVolumeAtIndex, found := token.GetVolumeAtIndex(1)
	if !found || actualVolumeAtIndex != expectedVolumeAtIndex {
		t.Errorf("expected volume at index %v, got %v", expectedVolumeAtIndex, actualVolumeAtIndex)
	}

	// Test GetTopHolderOwnershipPercentageAtIndex
	expectedOwnershipAtIndex := 60.0
	actualOwnershipAtIndex, found := token.GetTopHolderOwnershipPercentageAtIndex(1)
	if !found || actualOwnershipAtIndex != expectedOwnershipAtIndex {
		t.Errorf("expected ownership percentage at index %v, got %v", expectedOwnershipAtIndex, actualOwnershipAtIndex)
	}

	// Test GetTopHoldersAtIndex
	expectedHoldersAtIndex := holders[1].Holders
	actualHoldersAtIndex, found := token.GetTopHoldersAtIndex(1)
	if !found || len(actualHoldersAtIndex) != len(expectedHoldersAtIndex) || actualHoldersAtIndex[0].Holder != expectedHoldersAtIndex[0].Holder {
		t.Errorf("expected holders at index %v, got %v", expectedHoldersAtIndex, actualHoldersAtIndex)
	}
}
