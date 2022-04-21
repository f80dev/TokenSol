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
import {MetabossKey, showError, showMessage, words} from "../tools";
import {environment} from "../environments/environment";
import {NETWORKS} from "../definitions";
import {Token} from "./nfts/nfts.component";

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

  complete_token(r:any[]) : Promise<any[]> {
    return new Promise((resolve, reject) => {
      let rc: any[] = [];
      if(!r)reject(new Error("Empty list"))
      for (let e of r) {
        const accountInfo: any = SPLToken.AccountLayout.decode(e.account.data);
        accountInfo["pubkey"] = e.pubkey;
        const layoutInfo = SPLToken.MintLayout.decode(e.account.data);
        let explorer_domain=this.network=="devnet" ? "https://api-devnet.solscan.io" : "https://api.solscan.io"
        this.httpClient.get(explorer_domain+"/account?address=" + accountInfo.mint.toBase58()).subscribe((dt: any) => {
          this.httpClient.get(dt.data?.metadata?.data.uri).subscribe((data_sup: any) => {
            let token:Token = {
              address: dt.data.account,
              metadataPDA: {},
              mint: layoutInfo.mintAuthority.toBase58(),
              splMintInfo: this.add_solscan(layoutInfo),
              splTokenInfo:this.add_solscan(dt.data.tokenInfo),
              metadataOffchain: data_sup,
              metadataOnchain:this.add_solscan(dt.data.metadata),
              search:{
                collection:words(data_sup.collection),
                metadata:words(Object.values(data_sup.attributes))
              }

            }

            for(let creator of token.metadataOnchain?.data?.creators){
              for(let k of this.keys){
                if(creator.address==k.pubkey)creator.address=k.name;
              }
            }

            rc.push(token);
            if (rc.length == r.length) {
              resolve(rc);
            }
          }, (err) => {
            let token = {
              accountInfo:accountInfo,
              layoutInfo:layoutInfo,
              solscan:dt.data,
              offchain:{}
            };
            rc.push(token);
            if (rc.length == r.length) resolve(rc);
          })
        })
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




  get_tokens_from_owner(owner:string,function_name="by_owner") : Promise<any[]> {
    return new Promise((resolve,reject) => {
      if(!owner){
        reject();
      } else {

        if(this.network.indexOf("elrond")==-1){
          let publicKey=new PublicKey(owner);

          if(function_name=="by_owner"){
            this.connection.getTokenAccountsByOwner(publicKey,{programId: TOKEN_PROGRAM_ID},"confirmed").then((r:any)=> {
              this.complete_token(r.value).then(r => {
                resolve(r);
              })
            }).catch(err=>{
              reject(err);
            });
          }
        } else {
          this.httpClient.get(environment.server+"/api/nfts/?limit=40&account="+owner+"&network="+this.network).subscribe((r:any)=>{
            resolve(r);
          })
        }



        if(function_name=="by_delegate"){
          //TODO function en chantier
          this.httpClient.post("",{}).subscribe((r:any)=> {
            this.complete_token(r.value).then(r => {
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
        this.complete_token(r.value).then(r=>{resolve(r);})
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
}
