import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {$$, MetabossKey} from "../tools";
import {NFT} from "./nfts/nfts.component";

@Injectable({
  providedIn: 'root'
})
export class MetabossService {

  admin_key:MetabossKey | undefined;
  public keys:MetabossKey[]=[];

  constructor(
    private httpClient : HttpClient,
    private network:NetworkService
  )
  {}

  //http://localhost:4200/keys
  init_keys(network="elrond-devnet",with_balance=true) {
    return new Promise((resolve, reject) => {
      this.network.wait("Chargement des clés");
      if(this.network.isElrond() || this.network.isSolana()){
        this.httpClient.get<MetabossKey[]>(environment.server + "/api/keys/?network=" + network + "&with_private=true&with_balance="+with_balance).subscribe((r: MetabossKey[]) => {
          this.keys = r;
          this.network.wait();
          resolve(r);
        },()=>{
          $$("Probleme de chargement");
          reject();
        });
      }
      else {
        reject();
      }
    });
  }


  add_key(key:any,network="elrond-devnet",email=""){
    return this.httpClient.post(environment.server+"/api/keys/"+key["name"]+"/?network="+network+"&email="+email,key);
  }


  mint(token:NFT,sign=false,platform="nftstorage",network=""){
    return new Promise((resolve, reject) => {
      this.network.wait("Minage en cours sur "+network);
      this.httpClient.post(environment.server+"/api/mint/?keyfile="+this.admin_key?.name+"&sign="+sign+"&platform="+platform+"&network="+network,token).subscribe((r)=>{
        this.network.wait();
        resolve(r);
      },(err)=>{
        this.network.wait();
        reject(err);
      })
    });
  }




  update(nft_addr:string,new_value:string,field="uri",network="elrond-devnet") {
    return new Promise((resolve, reject) => {
      if(field=='uri'){
        this.httpClient.get(environment.server+"/api/update?url="+new_value+"&account="+this.admin_key+"&network="+network).subscribe((r:any)=>{
          resolve(true);
        })
      }
    });
  }


  update_obj(nft_addr:string,data:any,network="elrond-devnet") {
    return new Promise((resolve, reject) => {
      this.httpClient.post(environment.server+"/api/update_obj/?account="+nft_addr+"&keyfile="+this.admin_key?.name+"&network="+network,data).subscribe((r:any)=>{
        if(r.result=="error")
          reject(r.error);
        else
          resolve(r.out);
      })
    });
  }



  burn(nft_addr:string | undefined,network="elrond-devnet",delay=1) {
    return new Promise((resolve, reject) => {
      this.network.wait("En cours de destruction");
      this.httpClient.get(environment.server+"/api/burn?&delay="+delay+"&account="+nft_addr+"&keyfile="+this.admin_key?.name+"&network="+network).subscribe((r:any)=>{
        this.network.wait("");
        if(r.result=="error")
          reject(r.error);
        else
          resolve(r.out);
      })
    });
  }




  sel_key(account: string) {
    return new Promise((resolve, reject) => {
        let bc=false;
        for (let k of this.keys) {
          if (k.name == account) {
            this.admin_key = k;
            bc=true;
            resolve(k);
          }
        }
        if(!bc)reject(new Error(account + " not found"));
      })
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




  sign(nft_addr:string,creator_addr:string,network="elrond-devnet") {
    return new Promise((resolve, reject) => {
      this.httpClient.get(environment.server+"/api/sign?creator="+creator_addr+"&account="+nft_addr+"&keyfile="+this.admin_key?.name+"&network="+network).subscribe((r:any)=>{
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

  use(address: string, network: string) {
    return new Promise((resolve, reject) => {
      this.httpClient.get(environment.server+"/api/use?account="+address+"&keyfile="+this.admin_key?.name+"&network="+network).subscribe((r:any)=>{
        resolve(r);
      },(err)=>{
        reject(err);
      });
    });
  }

  del_key(name: string) {
    return this.httpClient.delete(environment.server+"/api/keys/"+name+"/?network="+this.network.network)
  }

  encrypte_key(name:string) {
    return this.httpClient.get(environment.server+"/api/encrypt_key/"+name)
  }
}
