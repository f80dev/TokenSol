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

@Injectable({
  providedIn: 'root'
})
export class NetworkService {

  private _network:string="devnet";
  private _connection: Connection=new Connection(clusterApiUrl("devnet"), 'confirmed');

  constructor() { }

  get_tokens(pubkey: PublicKey) {
    return new Promise((resolve, reject) => {
      this.connection.getTokenAccountsByOwner(pubkey, {
        programId: TOKEN_PROGRAM_ID,
      }).then((r) => {
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
    return this.connection.requestAirdrop(publicKey, LAMPORTS_PER_SOL).then(
      (airdropSignature: TransactionSignature) => {
        return this.connection.confirmTransaction(airdropSignature);
      }
    );
  }

  isMain() {
    return this._network=="mainnet";
  }
}
