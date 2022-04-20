import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {NetworkService} from "./network.service";
import {Observable} from "rxjs";
import {environment} from "../environments/environment";
import {$$, MetabossKey} from "../tools";
import {PublicKey} from "@solana/web3.js";


@Injectable({
  providedIn: 'root'
})
export class MetabossService {

  admin_key:MetabossKey | undefined;

  constructor(
    private httpClient : HttpClient,
    private network:NetworkService
  ) {
    this.keys().subscribe((r)=>{
      this.admin_key=r[0];
    })
  }


  //http://localhost:4200/keys
  keys(): Observable<MetabossKey[]> {
    return this.httpClient.get<MetabossKey[]>(environment.server+"/api/keys/");
  }


  add_key(key:any){
    return this.httpClient.post(environment.server+"/api/keys/",key);
  }


  mint(token:any,sign=false,platform="nftstorage",network=""){
    return new Promise((resolve, reject) => {
      network=(network=="") ? this.network.network : "devnet"
      this.network.wait("Minage en cours sur "+network);
      this.httpClient.post(environment.server+"/api/mint/?keyfile="+this.admin_key?.name+"&sign="+sign+"&platform="+platform+"&network="+network,token).subscribe((r)=>{
        resolve(r);
      },(err)=>{
        reject(err);
      })
    });
  }

  //recoit un objet aux propriétés filename & content
  upload(file: any ,platform="nftstorage"){
    return new Promise((resolve, reject) => {
      this.network.wait("Chargement du fichier");
      this.httpClient.post(environment.server+"/api/upload/?platform="+platform,file).subscribe((r)=>{
        resolve(r);
      },(err)=>{
        reject(err);
      })
    });
  }


  update(nft_addr:string,new_value:string,field="uri",network="devnet") {
    return new Promise((resolve, reject) => {
      if(field=='uri'){
        this.httpClient.get(environment.server+"/api/update?url="+new_value+"&account="+this.admin_key+"&network="+network).subscribe((r:any)=>{
          resolve(true);
        })
      }
    });
  }


  update_obj(nft_addr:PublicKey,data:any,network="devnet") {
    return new Promise((resolve, reject) => {
      this.httpClient.post(environment.server+"/api/update_obj/?account="+nft_addr.toBase58()+"&keyfile="+this.admin_key?.name+"&network="+network,data).subscribe((r:any)=>{
        resolve(true);
      })
    });
  }



  burn(nft_addr:string,network="devnet") {
    return new Promise((resolve, reject) => {
      this.network.wait("En cours de destruction");
      this.httpClient.get(environment.server+"/api/burn?&account="+nft_addr+"&keyfile="+this.admin_key?.name+"&network="+network).subscribe((r:any)=>{
        this.network.wait("");
        resolve(true);
      })
    });
  }




  sel_key(account: string) {
    return new Promise((resolve, reject) => {
      this.keys().subscribe((r) => {
        for (let k of r) {
          if (k.name == account) {
            this.admin_key = k;
            resolve(k);
          }
        }
        reject(new Error(account + " not found"));
      })
    });
  }



  archive(tokens: any) {
    return new Promise((resolve, reject) => {
      this.httpClient.post(environment.server+"/api/export/",tokens).subscribe((r)=>{
        resolve(r);
      },(err)=>{
        reject(err);
      })
    });
  }




  sign(nft_addr:string, address:string,network="devnet") {
    return new Promise((resolve, reject) => {
      this.httpClient.get(environment.server+"/api/sign?account="+nft_addr+"&keyfile="+address+"&network="+network).subscribe((r:any)=>{
        resolve(r);
      },(err)=>{
        reject(err);
      });
    });
  }

  airdrop(amount: number) {
    if(this.admin_key?.pubkey){
      // @ts-ignore
      this.network.airdrop(this.admin_key?.pubkey).then(()=>{});
    }

  }
}
