-- CreateTable
CREATE TABLE "Tokens" (
    "ID" SERIAL NOT NULL,
    "PublicKey" TEXT NOT NULL,
    "MetaName" TEXT,
    "MetaTicker" TEXT,
    "TokenSupply" BIGINT NOT NULL DEFAULT 0,
    "TokenDecimals" INTEGER NOT NULL DEFAULT 0,
    "MetaChangeAuthority" TEXT NOT NULL,
    "FreezeAuthority" TEXT NOT NULL,
    "MintAuthority" TEXT NOT NULL,
    "Owner" TEXT NOT NULL,
    "InitialMint" TIMESTAMP(3),
    "IPO" TIMESTAMP(3),
    "LargestHolders" JSONB,
    "Rugpull" BOOLEAN NOT NULL DEFAULT false,
    "RugpullDate" TIMESTAMP(3),

    CONSTRAINT "Tokens_pkey" PRIMARY KEY ("ID")
);

-- CreateIndex
CREATE UNIQUE INDEX "Tokens_PublicKey_key" ON "Tokens"("PublicKey");
