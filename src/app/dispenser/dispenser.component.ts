import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute, Router} from "@angular/router";
import {getParams, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {MatDialog} from "@angular/material/dialog";

import {Operation} from "../../operation";
import {NFT} from "../../nft";

@Component({
  selector: 'app-dispenser',
  templateUrl: './dispenser.component.html',
  styleUrls: ['./dispenser.component.css']
})
export class DispenserComponent implements OnInit {
  nfts: NFT[]=[];
  message="";
  operation: any;
  dest="";


  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public dialog:MatDialog,
    public router:Router,
    public toast:MatSnackBar,
    public alias:AliasPipe
  ) { }

  //test: http://127.0.0.1:4200/dispenser?ope=calvi22_devnet&toolbar=false/dispenser?ope=calvi22_devnet
  ngOnInit(): void {
    let limit=Number(this.routes.snapshot.queryParamMap.get("limit") || "1000") ;
    getParams(this.routes).then((params:any)=>{
      this.network.get_operations(params["ope"]).subscribe((operation:Operation)=>{
        this.operation=operation;
        this.message="Chargement des NFTs";
        this.network.get_tokens_to_send(operation.id,"dispenser",limit).subscribe((nfts:any) => {
          this.nfts=[];
          this.message="";
          for(let nft of nfts){
            if(nft.marketplace.quantity>0){
              nft.style={opacity:1};
            } else {
              nft.style={opacity:0.3};
            }
            if(!nft.marketplace.hasOwnProperty("price"))nft.marketplace.price=0;
            if(operation.dispenser && nft.marketplace.price==0 && (!operation.dispenser.collections || operation.dispenser.collections.length==0 || operation.dispenser.collections.indexOf(nft.collection["id"])>-1))
              this.nfts.push(nft);
          }
        });
      })
    });
  }

  send(nft: any) {
    if(nft.quantity==0){
      showMessage(this,"Ce NFT ne peut plus être miné");
      return;
    }

    nft.price=0;
    this.router.navigate(["dealermachine"],{queryParams:{param:setParams({
          token:nft,
          price:0,
          ope: this.operation.id,
          selfWalletConnexion:false,
          mining:this.operation.lazy_mining
        })}})

      // if(this.dest){
      //   this.alias.transform(this.dest,"pubkey")
      //   this.message="Minage et envoi en cours sur le wallet "+this.dest;
      //   this.network.mint_for_contest(this.dest,nft.collection.name+"_"+nft.symbol,this.operation,this.operation.dispenser.miner,this.operation.metadata_storage).subscribe((r:any)=>{
      //     this.message="";
      //     showMessage(this,"Envoyé");
      //   },(err:any)=>{
      //     showError(this,err);
      //   });
      // }else{
      //   showMessage(this,"Envoi annulé");
      // }

  }
}
