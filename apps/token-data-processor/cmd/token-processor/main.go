package main

import (
	"context"
	"sync"

	"github.com/Zaydo123/token-processor/internal/config"
	"github.com/Zaydo123/token-processor/internal/redis/listeners"
	"github.com/Zaydo123/token-processor/internal/redis/tasks/update"
	"github.com/Zaydo123/token-processor/internal/token/models"
)

func main() {

	wg := new(sync.WaitGroup)

	// ================== Load configuration ==================

	config.LoadEnv(5)
	config.ParseEnv()

	// ================== Start services ==================
	var ctx = context.Background()

	// tokenMap := make(map[string] models.Token)
	// token model should be a pointer
	tokenMap := make(map[string]*models.Token)

	wg.Add(1)
	go listeners.StartServices(ctx, wg, &tokenMap)

	// Cache update task - never ends
	wg.Add(1)
	go update.UpdateTask(&tokenMap)

	wg.Wait()

}
