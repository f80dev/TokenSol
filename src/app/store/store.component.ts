import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {setParams, showMessage} from "../../tools";
import {NFT} from "../nfts/nfts.component";

@Component({
  selector: 'app-store',
  templateUrl: './store.component.html',
  styleUrls: ['./store.component.css']
})
export class StoreComponent implements OnInit {
  operation: any;
  nfts: NFT[]=[];
  message: string="";
  title:string="";
  bgcolor: string="white";

  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.bgcolor=this.routes.snapshot.queryParamMap.get("bgcolor") || "white";
    this.title=this.routes.snapshot.queryParamMap.get("title") || "";
    this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((ope:any)=> {
      this.operation = ope;
      this.message="Chargement des NFTs";
      this.network.get_tokens_to_send(ope.id,"store",50).subscribe((nfts:any) => {
        this.nfts=[];
        for(let nft of nfts){
          nft.marketplace={price:0,quantity:1};
          for(let c of this.operation.store.collections || []){
            if(c.name==nft.collection.name)nft.marketplace={price:c.price,quantity:nft.balance};
          }
          this.nfts.push(nft);
        }
        this.message="";
      });
    },(err)=>{
      showMessage(this,"Operation impossible à charger");
    })
  }

  buy(nft: NFT) {
    let param=setParams({
      token:nft,
      ope:this.operation.id,
      selfWalletConnexion:false,
      mining:this.operation.store.miner
    })
    this.router.navigate(["dealermachine"],{queryParams:{param:param}});
  }
}
