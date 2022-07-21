import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute, Router} from "@angular/router";
import {encrypt, setParams, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";

@Component({
  selector: 'app-dispenser',
  templateUrl: './dispenser.component.html',
  styleUrls: ['./dispenser.component.css']
})
export class DispenserComponent implements OnInit {
  nfts: any[]=[];
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
    this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((operation:any)=>{
      this.operation=operation;
      this.message="Chargement des NFTs";
      this.network.get_tokens_to_send(operation.id,"dispenser",limit).subscribe((nfts:any) => {
        this.nfts=[];
        this.message="";
        for(let nft of nfts){
          if(nft.quantity>0){
            nft.opacity==1;
          } else {
            nft.opacity=0.3;
          }

          this.nfts.push(nft);
        }
      });
    })
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
