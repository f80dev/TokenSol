import { Injectable } from '@angular/core';
import {
  clusterApiUrl,
  Connection,
  LAMPORTS_PER_SOL,
  PublicKey, AccountInfo,
  RpcResponseAndContext, SignatureResult,
  TransactionSignature
} from "@solana/web3.js";
import {AccountLayout, TOKEN_PROGRAM_ID} from "@solana/spl-token";
import * as SPLToken from "@solana/spl-token";
import {TokenListProvider} from "@solana/spl-token-registry";
import {HttpClient} from "@angular/common/http";

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private _network:string="devnet";
  private _connection: Connection=new Connection(clusterApiUrl("devnet"), 'confirmed');
  waiting: string="";

  constructor(
    private httpClient : HttpClient
  ) { }

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
      this._connection=new Connection(clusterApiUrl(this._network), 'confirmed');
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

  complete_token(r:any[]) : Promise<any[]> {
    return new Promise((resolve, reject) => {
      let rc: any[] = [];
      if(!r)reject(new Error("Empty list"))
      for (let e of r) {
        const accountInfo: any = SPLToken.AccountLayout.decode(e.account.data);
        accountInfo["pubkey"] = e.pubkey;
        const layoutInfo = SPLToken.MintLayout.decode(e.account.data);
        this.httpClient.get("https://api-devnet.solscan.io/account?address=" + accountInfo.mint.toBase58()).subscribe((dt: any) => {
          this.httpClient.get(dt.data.metadata.data.uri).subscribe((data_sup: any) => {
            let tokenInfo = {accountInfo:accountInfo, layoutInfo:layoutInfo, solscan:dt.data, offchain:data_sup};
            rc.push(tokenInfo);
            if (rc.length == r.length) resolve(rc);
          }, (err) => {
            let tokenInfo = {...accountInfo, ...layoutInfo, ...dt.data};
            rc.push(tokenInfo);
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


  get_tokens_from_owner(owner:PublicKey) : Promise<any[]> {
    return new Promise((resolve,reject) => {
      this.connection.getTokenAccountsByOwner(owner,{programId: TOKEN_PROGRAM_ID},"confirmed").then((r:any)=> {
        this.complete_token(r.value).then(r => {
          resolve(r);
        })
      });
    });
  }

  get_nfts_from_miner(miner:PublicKey) : Promise<any[]> {
    return new Promise((resolve,reject) => {
      this.connection.getProgramAccounts(miner,"confirmed").then((r:any)=>{
        this.complete_token(r.value).then(r=>{resolve(r);})
      })
    });
  }
}
