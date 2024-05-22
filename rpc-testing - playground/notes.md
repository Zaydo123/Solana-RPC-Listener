# Quick rpc response notes

![alt text](image.png)


## RPC Response
- Json.result: The result of the rpc call
- result.context.slot is the block number
- result.value.pubKey (in context of spltoken2022) is the public key of the token account
- result.account.lamports - the balance of the account in lamports
- result.account.data - the data of the account
- result.account.data.program - the program id (ex spl-token-2022)
- result.account.data.parsed.type - the type of the account (mint or account, yet to see others)
- result.account.data.parsed.info - juicy info about the spl token
- info.decimals - the most decimals that the token can have
- info.freezeAuthority - the freeze authority of the token (null if none else the public key)
- info.isInitialized - if the token is initialized or not
- info.mintAuthority - the mint authority of the token (null if none else the public key)
- info.supply - the supply of the token
- parsed.space - the space of the account in bytes (i think)
- data.owner - the owner of the account (usually spl token address)
- data.executable - if the account is executable or not
- data.rentEpoch - the rent epoch of the account (usually max int64 unless u dont meet rent exemption)
- result.subscription - the subscription id of the rpc call



- From solana : "Tokens when initially created by spl-token have no supply"