import {Collection} from "./operation";

export interface Creator {
  address:string
  verified:number
  share:number
}
export interface SplTokenInfo {
  mint:string
  owner:string
  amount: number
  state:number
  address:string
  isFrozen:boolean
}
export interface SplMintInfo {
  mintAuthority:string
  supply:string
  decimal:number
}
export interface Attribute {
  trait_type:string
  value:string
}
export interface MetadataExternal {
  name:string
  description:string
  external_url:string
  image: string
  seller_fee_basis_points: number
  attributes:Attribute[]
  collection: string
  properties:{
    files:{uri:string,type:string}[]
    caterogy:string
    creators:Creator[]
  }
  issuer:string
}

export interface MetadataOnChain {
  key:number | undefined
  updateAuthority:string
  mint:string,
  primarySaleHappened:number
  isMutable:number
  type:string
  data:{
    name:string
    symbol:string
    uri:string
    sellerFeeBasisPoints:number
    creators:Creator[]
  }
}
export interface Search {
  collection:string
  metadata:string
}



export interface NFT {
  collection:Collection
  symbol:string
  network: string | undefined
  attributes:{
    trait_type:string
    value: string
  }[]
  name:string
  description:string
  visual:string
  creators: any[]
  address:string | undefined
  royalties:number
  owner:string | undefined
  marketplace: {
    price: number
    quantity: number
  } | undefined
  files:any[]
  solana: any | undefined
  message: string | undefined
  style: any | undefined
}

export interface SolanaToken {
  mint:string,
  network: string
  address: string,
  splTokenInfo : SplTokenInfo | undefined
  splMintInfo : SplMintInfo | undefined,
  metadataPDA:any,
  metadataOnchain:MetadataOnChain,
  metadataOffchain:MetadataExternal,
  search:Search
}
