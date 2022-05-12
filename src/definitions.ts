export let PERMS:any={
  "799C3Tr6gxdwspPoDEBvFGgLCyzMrSrFjd3CkVW6ukar":["validate","buy","about","help","reload","wallet","keys","mint"],
  "Ee2zEFPiNhs7ZxuRg7aA1J4qDFNM5yQWH4CtzP7tssAt":["validate","buy","about","help","reload","wallet","keys","mint"],
  "anonymous":['help','about',"mint","keys","manage","creator"],
  "connected":['buy','reload','help','about',"wallet","mint","keys","manage"]
}

export const NFT_STORAGE_TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkaWQ6ZXRocjoweEQ4ZTk2MERCRDEwYjVlNTExMTU5REI5RDk3NzQ0MkI2ODI1OWU1MTQiLCJpc3MiOiJuZnQtc3RvcmFnZSIsImlhdCI6MTY0NTcyMzU4MDU0MSwibmFtZSI6Im5mbHVlbnQifQ.5rzoF_fn5iZJLY2nD-yTIt3RoxWKoOuh_rPZ-prwnds';

export const QUOTA=800000

export const NETWORKS=["devnet","mainnet","elrond-devnet","elrond-mainnet","FTX"]


export const PLATFORMS=[
  {label:"NFT storage",value:"nftstorage"},
  {label:"IPFS",value:"ipfs"},
  {label:"Infura (IPFS)",value:"infura"}
]
