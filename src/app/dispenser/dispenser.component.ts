import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";
import {showError, showMessage} from "../../tools";
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


  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public dialog:MatDialog,
    public toast:MatSnackBar,
    public alias:AliasPipe
  ) { }

  //test: http://127.0.0.1:4200/dispenser?ope=calvi22_devnet&toolbar=false/dispenser?ope=calvi22_devnet
  ngOnInit(): void {
    let limit=Number(this.routes.snapshot.queryParamMap.get("limit") || "1000") ;
    this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((operation:any)=>{
      this.operation=operation;
      this.network.get_tokens_for_dispenser(operation.id,limit).subscribe((nfts:any) => {
        this.nfts=[];
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
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Destinataire de ce NFT",
          result: "paul.dudule@gmail.com",
          type: "text",
          placeholder:"indiquer son adresse email ou son wallet",
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((addr:string) => {
      if(addr){
        this.alias.transform(addr,"pubkey")
        this.message="Minage et envoi en cours sur le wallet "+addr;
        this.network.mint_for_contest(addr,nft.collection.name+"_"+nft.symbol,this.operation,this.operation.dispenser.miner,this.operation.metadata_storage).subscribe((r:any)=>{
          this.message="";
          showMessage(this,"Envoyé");
        },(err:any)=>{
          showError(this,err);
        });
      }else{
        showMessage(this,"Envoi annulé");
      }

    });

  }
}
