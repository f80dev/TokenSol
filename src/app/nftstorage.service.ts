import { Injectable } from '@angular/core';
import {NFTStorage, Token} from "nft.storage";
import {NFT_STORAGE_TOKEN} from "../definitions"

@Injectable({
  providedIn: 'root'
})
export class NftstorageService {

  client= new NFTStorage({ token: NFT_STORAGE_TOKEN })

  constructor() {

  }

  store(data:any):Promise<string> {
    return new Promise((resolve,reject) => {
      //voir https://nftstorage.github.io/nft.storage/client/
      return this.client.store(data).then((r)=>{
        resolve(r.url);
      }).catch((err)=>{
        debugger
        reject(err);
      });
    });
  }



}
