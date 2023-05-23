import { Component, OnInit } from '@angular/core';
import {NFT} from "../../nft";
import {apply_params, getParams} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-gallery',
  templateUrl: './gallery.component.html',
  styleUrls: ['./gallery.component.css']
})
export class GalleryComponent implements OnInit {
  nfts: NFT[] = [];
  address:string="";
  network: string="";
  delay_between=3;
  size=80;
  collection: string="";
  showNfluentWalletConnect=true;
  visual: string="";
  nft_title:string="";
  canChange: boolean=true;
  private quota_min: number=10
  background: string="";

  constructor(
      public routes:ActivatedRoute,
      public api:NetworkService
  ) { }

  async ngOnInit() {
    let params:any=await getParams(this.routes)
    apply_params(this,params,environment);

    this.collection=params.collection || ""
    if(this.collection.length>0){
      this.api.get_nfts_from_collection(this.collection,this.network).subscribe((r)=>{
        this.nfts=r.nfts;
      })
    }else{
      this.address=params.address || params.miner || "";
      this.on_authen({provider: undefined, strong: false, address:this.address});
    }

    this.delay_between=params.delay_between || 3;
    this.canChange=(params.chanChange=="true")
    this.size=Number(params.size || "80")
    this.quota_min=Number(params.quota_min || "10")
    this.showNfluentWalletConnect=(params.showNfluentWalletConnect =="true");

  }


  async on_authen($event: { strong: boolean; address: string; provider: any }) {
    if($event.address.length>0){
      let r:any=await this.api.get_tokens_from("owner",$event.address,100,false,null,0,this.network)
      if(r.result && r.result.length>this.quota_min){
        this.address=$event.address;
        this.nfts=r.result;
      }
    }
  }

  update_nft($event: NFT) {
    this.nft_title=$event.name;
  }
}
