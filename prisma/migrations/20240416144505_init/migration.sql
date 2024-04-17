-- AlterTable
ALTER TABLE "APIKey" ADD COLUMN     "active" BOOLEAN NOT NULL DEFAULT true,
ADD COLUMN     "credit" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "ipWhitelist" TEXT[] DEFAULT ARRAY[]::TEXT[],
ADD COLUMN     "rateLimit" INTEGER NOT NULL DEFAULT 0,
ADD COLUMN     "usage" INTEGER NOT NULL DEFAULT 0;
