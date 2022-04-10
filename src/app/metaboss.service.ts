import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {NetworkService} from "./network.service";


@Injectable({
  providedIn: 'root'
})
export class MetabossService {

  server="http://localhost:9999"

  constructor(
    private httpClient : HttpClient,
    private network:NetworkService
  ) { }



  init(){

  }


  update(nft_addr:string,new_value:string,field="uri") {
    return new Promise((resolve, reject) => {
      if(field=='uri'){
        this.httpClient.get(this.server+"/api/update?url="+new_value+"&account="+nft_addr).subscribe((r:any)=>{
          resolve(true);
        })
      }
    });
  }

  update_obj(nft_addr:string,data:any) {
    return new Promise((resolve, reject) => {
      this.httpClient.post(this.server+"/api/update_obj/? account="+nft_addr,data).subscribe((r:any)=>{
        resolve(true);
      })
    });
  }



  burn(nft_addr:string) {
    return new Promise((resolve, reject) => {
      this.network.waiting="En cours de destruction";
      this.httpClient.get(this.server+"/api/burn?&account="+nft_addr).subscribe((r:any)=>{
        this.network.waiting="";
        resolve(true);
      })
    });
  }
}
