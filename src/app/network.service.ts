import { Injectable } from '@angular/core';
import {
  clusterApiUrl,
  Connection,
  LAMPORTS_PER_SOL,
  PublicKey,
  RpcResponseAndContext, SignatureResult,
  TransactionSignature
} from "@solana/web3.js";
import {TOKEN_PROGRAM_ID} from "@solana/spl-token";
import * as SPLToken from "@solana/spl-token";
import {TokenListProvider} from "@solana/spl-token-registry";
import {HttpClient} from "@angular/common/http";
import {$$,MetabossKey,words} from "../tools";
import {environment} from "../environments/environment";

import {Token} from "./nfts/nfts.component";
import {Layer} from "./creator/creator.component";

export enum type_addr {
  "owner",
  "miner"
}

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private _network:string="devnet";
  private _connection: Connection=new Connection(clusterApiUrl("devnet"), 'confirmed');
  waiting: string="";
  keys:MetabossKey[]=[];

  constructor(
    private httpClient : HttpClient
  ) {

  }



  get_tokens(pubkey: PublicKey,f:Function) {
    return new Promise((resolve, reject) => {
      f(pubkey, {programId: TOKEN_PROGRAM_ID})
        .then((r:any) => {
          let rc = [];
          for (let t of r.value) {
            rc.push(t);
          }
          resolve(rc);
        }).catch((err:Error)=>{reject(err)});
    });
  };


  get network(): string {
    return this._network;
  }

  set network(value: string) {
    this._network = value;
    if(this._network){
      // @ts-ignore
      let network_name=(value=="devnet") ? "devnet" : "mainnet-beta";
      // @ts-ignore
      this._connection=new Connection(clusterApiUrl(network_name), 'confirmed');
    }

  }

  get connection(): Connection {
    return this._connection;
  }

  set connection(value: Connection) {
    this._connection = value;
  }

  getBalance(publicKey: PublicKey) : Promise<number> {
    return new Promise((resolve, reject) => {
      this.connection.getBalance(publicKey).then(r => {resolve(r/1000000000);});
    });
  }

  airdrop(publicKey: PublicKey) : Promise<RpcResponseAndContext<SignatureResult>> {
    this.waiting="Airdrop en cours";

    return this.connection.requestAirdrop(publicKey, LAMPORTS_PER_SOL).then(
      (airdropSignature: TransactionSignature) => {
        this.waiting="";
        return this.connection.confirmTransaction(airdropSignature);
      }
    );


  }

  add_solscan(token:any) : any{
    for(let k in token){
      let value=token[k];
      if(value && typeof value==="object" && value.constructor.name === "PublicKey"){
        value='https://solscan.io/address/'+value.toBase58()+'?cluster='+this._network;
        token[k+"_explorer"]=value;
      }
    }
    return token;
  }


  create_token(offchain:any,mintAuthority:string,mintAddress:string,data_sup:any,splMintInfo:any,owner:string) {
    let token = {
      address: mintAddress,
      metadataPDA: {},
      mint: data_sup.metadata.mint,
      splMintInfo: splMintInfo,
      splTokenInfo:{address: "", amount: "", isFrozen: false, mint: "", state: 0, owner:owner},
      metadataOffchain: offchain,
      metadataOnchain:data_sup.metadata,
      search:{
        collection:words(data_sup.collection),
        metadata:words(Object.values(offchain.attributes))
      }
    }

    return token;
  }


  solscan_info(mintAddress:string){
    let explorer_domain=(this.network=="devnet" ? "https://api-devnet.solscan.io" : "https://api.solscan.io")
    return new Promise((resolve, reject) => {
      if(mintAddress){
        this.httpClient.get(explorer_domain+"/account?address=" + mintAddress).subscribe((dt: any) => {
          this.connection.getAccountInfo(new PublicKey(dt.data.tokenInfo.tokenAuthority), "confirmed").then((resp: any) => {
            let owner = resp.owner.toBase58();
            dt.owner=owner;
            resolve(dt);
          },(err:any)=>{$$("erreur ",err);reject(err);})
        });
      }
    });
  }


  build_token_from_solscan(mintAddress:string):Promise<Token> {
    return new Promise((resolve, reject) => {
      this.solscan_info(mintAddress).then((dt:any)=>{
        if(!dt.data?.hasOwnProperty("metadata")){
          reject("NFT introuvable");
        } else {
          let url_metadata=dt.data?.metadata?.data.uri;
          let owner="";
          let mintAuthority=dt;
          if(dt.data.metadata.primarySaleHappened==0)owner=dt.data.metadata.updateAuthority;
          this.httpClient.get(url_metadata).subscribe((offchain:any)=>{
            resolve(this.create_token(offchain,mintAuthority,dt.data.metadata.mint,dt.data,dt.data.tokenInfo,owner));
          })
        }
      })
    });
  }


  complete_token(owner:string,r:any[]) : Promise<any[]> {
    $$("Completion des tokens");
    return new Promise((resolve, reject) => {
      let rc: any[] = [];
      if(!r)reject(new Error("Empty list"))

      for (let e of r) {
        if(e.account && e.account.data){
          let accountInfo:any = SPLToken.AccountLayout.decode(e.account.data);
          accountInfo["pubkey"] = e.pubkey;
          let layoutInfo = SPLToken.MintLayout.decode(e.account.data);
          let mintAddress=accountInfo.mint.toBase58();
          let mintAuthority=layoutInfo.mintAuthority.toBase58();

          this.solscan_info(mintAddress).then((dt:any)=>{
            let url_metadata=dt.data?.metadata?.data.uri;
            this.httpClient.get(url_metadata).subscribe((offchain:any)=>{
              rc.push(this.create_token(offchain,mintAuthority,dt.data.metadata.mint,dt.data,layoutInfo,owner));
              if(rc.length==r.length)resolve(rc);
            })
          })

        }
      }
    });
  }





  isMain() {
    return this._network=="mainnet";
  }


  all_nfts() : Promise<any[]> {
    return new Promise((resolve,reject) => {
      new TokenListProvider().resolve().then((tokens) => {
        const tokenList = tokens.filterByClusterSlug(this._network).getList();
        resolve(tokenList);
      }).catch(err => {
        reject(err);
      });
    });
  }


  build_token_from_ftx(t:any) : Token {
    let l_attributes=t.attributesList;
    l_attributes.push({trait_type:"redeemable",value:t.redeemable});
    l_attributes.push({trait_type:"redeemed",value:t.redeemed});
    let token:Token={
      splMintInfo: undefined,
      splTokenInfo: undefined,
      mint:t.solMintAddress,
      address:t.solMintAddress,
      metadataPDA:{},
      metadataOffchain: {
        seller_fee_basis_points: t.royaltyFeeRate*100,
        issuer:t.issuer,
        attributes:l_attributes,
        collection: {name: t.collection},
        name: t.name,
        description: t.description,
        image: t.imageUrl,
        external_url: "",
        properties: {
          files:[
            {uri:t.imageUrl,type:""},{uri:t.animationUrl,type:""}
          ],
          caterogy:"",
          creators:[]
        },
      },
      metadataOnchain:{
        type:"nft",
        updateAuthority:"",
        mint:t.solMintAddress,
        key:t.id,
        data:{
          symbol:"",
          name:t.name,
          uri:"",
          sellerFeeBasisPoints:t.royaltyFeeRate*100,
          creators:[]
        },
        isMutable:0,
        primarySaleHappened:0
      },
      search:{collection:t.collection,metadata:""}
    }
    return token;
  }


  get_tokens_from(type_addr:string,addr:string) : Promise<any[]> {
    $$("Recherche de token par "+type_addr)
    return new Promise((resolve,reject) => {
      if(addr==null){
        reject();
      } else {
        if(this.network.indexOf("elrond")==-1){
          let func:any=null;

          if(type_addr=="FTX_account"){
            this.get_tokens_from_ftx(addr).then((tokens:any)=>{
              let rc:Token[]=[];
              for(let t of tokens){
                let token:Token=this.build_token_from_ftx(t);
                if(tokens.length<10){
                  this.solscan_info(t.solMintAddress).then((dt:any)=>{
                    token.metadataOnchain=dt.data.metadata
                    rc.push(token);
                    if(rc.length==tokens.length)resolve(rc);
                  })
                } else {
                  rc.push(token);
                }
              }
              if(tokens.length>10)resolve(rc);
            });
          }

          if(type_addr=="owner"){
            this.connection.getTokenAccountsByOwner(new PublicKey(addr),{programId: TOKEN_PROGRAM_ID},"confirmed").then((result:any)=> {
              let values=result.value;
              $$(values.length+" nfts trouvés");

              this.complete_token(addr,values).then(r => {
                resolve(r);
              }).catch((err)=>{
                $$("erreur ",err);
                reject(err);
              })
            }).catch((err:any)=>{
              $$("erreur ",err);
              reject(err);
            });
          }

          if(type_addr=="token"){
            this.build_token_from_solscan(addr).then((token:Token)=>{
              resolve([token]);
            }).catch((err)=>{
              reject(err);
            });
            return;
          }



        } else {
          //Listing elrond
          this.httpClient.get(environment.server+"/api/nfts/?limit=40&account="+addr+"&network="+this.network).subscribe((r:any)=>{
            resolve(r);
          })
        }



        if(type_addr=="miner"){
          //TODO function en chantier
          this.httpClient.get(environment.server+"/api/token_by_delegate/?account="+addr+"&network="+this.network).subscribe((r:any)=> {
            this.complete_token(addr,r.value).then(r => {
              resolve(r);
            })
          });
        }


      }
    });
  }

  get_nfts_from_miner(miner:PublicKey) : Promise<any[]> {
    return new Promise((resolve,reject) => {
      this.connection.getProgramAccounts(miner,"confirmed").then((r:any)=>{
        this.complete_token(miner.toBase58(),r.value).then(r=>{resolve(r);})
      })
    });
  }

  wait(message: string) {
    this.waiting=message;
    setTimeout(()=>{this.waiting=""},10000);
  }

  isElrond() {
    return this.network.indexOf("elrond")>-1;
  }

  isSolana() {
    return this.network=="devnet" || this.network=="mainnet";
  }

  get_nfts_balance_from_ftx(){
    return this.httpClient.get("https://ftx.us/api/nft/balances")
  }

  private get_tokens_from_ftx(filter: string) {
    return new Promise((resolve,reject) => {

      let key="solMintAddress";
      let value="!none";
      if(filter.length<40 || filter.length>50){
        key="collection";
        value=filter;
      }
      let url=environment.server+"/api/ftx/tokens/";
      $$("recherche sur "+url);
      this.httpClient.get(url).subscribe(((r:any)=>{
        let rc:any[]=[];
        $$(r.results.length+" NFTs identifié, croisement avec "+filter+" sur la collection");
        for(let token of r.results){
          if(filter.length==0 || token.collection.indexOf(filter)>-1)
            rc.push(token);
        }
        resolve(rc);
      }),(err)=>{
        reject(err);
      });
    });
  }

  get_list_tokens() {
    return this.httpClient.get(environment.server+"/api/get_list");
  }

  add_layer(l: any) {
    return this.httpClient.post(environment.server+"/api/layers/",l);
  }

  get_collection(limit: number,file_format:string) {
    return this.httpClient.get(environment.server+"/api/collection/?name="+file_format+"&format=preview&limit="+limit);
  }

  create_text_layer(x: number, y: number, text_to_add: string,l:Layer) {
    return this.httpClient.post(environment.server+"/api/layers/",
      {x:x,y:y,
        text:text_to_add,
        name:l.name,
        unique:l.unique,
        indexed:l.indexed,
        width:l.width,height:l.height,
        fontstyle:l.fontstyle});
  }

  reset_collection() {
    return this.httpClient.get(environment.server+"/api/reset_collection/");
  }

  save_config(name:string,body:any) {
    return this.httpClient.post(environment.server+"/api/save_config/"+name+"/",body);
  }

  load_config(name:string) {
    return this.httpClient.get(environment.server+"/api/configs/"+name+"/?format=json");
  }

  list_config() {
    return this.httpClient.get(environment.server+"/api/configs/");
  }

  list_installed_fonts() {
    return this.httpClient.get(environment.server+"/api/fonts/");
  }

  isValideToken(operation: string, query: string) {
    return this.httpClient.get(environment.server+"/api/validate/?ope="+operation+"&q="+query);
  }
}
