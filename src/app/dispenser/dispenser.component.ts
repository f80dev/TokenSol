import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute, Router} from "@angular/router";
import {$$, getParams, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {MatDialog} from "@angular/material/dialog";

import {Operation} from "../../operation";
import {NFT} from "../../nft";
import {Clipboard} from "@angular/cdk/clipboard";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-dispenser',
  templateUrl: './dispenser.component.html',
  styleUrls: ['./dispenser.component.css']
})
export class DispenserComponent implements OnInit {
  nfts: NFT[]=[];
  message="";
  operation: Operation | undefined;
  dest="";
  miner="";


  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public dialog:MatDialog,
    public router:Router,
    public toast:MatSnackBar,
    public alias:AliasPipe,
    public clipboardService:Clipboard
  ) { }

  //test: http://127.0.0.1:4200/dispenser?ope=calvi22_devnet&toolbar=false/dispenser?ope=calvi22_devnet
  ngOnInit(): void {
    let limit=Number(this.routes.snapshot.queryParamMap.get("limit") || "1000") ;
    getParams(this.routes).then((params:any)=>{
      this.message="Préparation de la page";
      this.network.get_operations(params["ope"]).subscribe((operation:Operation)=>{
        this.operation=operation;
        this.miner=params.hasOwnProperty("miner") ? params["miner"] : operation.lazy_mining?.networks[0].miner;
        this.message="Chargement des NFTs";
        this.network.get_tokens_to_send(operation.id,"dispenser",limit).subscribe((nfts:any) => {
          this.nfts=[];
          this.message="";
          for(let nft of nfts){
            if(nft.marketplace.quantity>0 && (nft.owner=='' || nft.owner==this.miner)){
              nft.style={opacity:1};
            } else {
              nft.style={opacity:0.3,cursor:"not-allowed",pointerEvents:"none"};
              nft.message="Déjà distribué"
            }
            nft.message=nft.owner+" - "+nft.address;
            if(!nft.marketplace.hasOwnProperty("price"))nft.marketplace.price=0;

            $$("Evaluation de la possibilité d'ajouté le NFT");
            let canAdd=nft.address.startsWith("db_");
            if(operation.dispenser){
              if(!canAdd)canAdd=(nft.marketplace.price==0 && nft.owner==nft.creators[0]);
              if(canAdd)canAdd=(!operation.dispenser.collections || operation.dispenser.collections.length==0 || operation.dispenser.collections.indexOf(nft.collection["id"])>-1)
            }
            if(canAdd)this.nfts.push(nft);

          }
        });
      })
    });
  }

  get_nft_link(nft:any){
    if(this.operation)
      return setParams({
        token: nft,
        price: 0,
        section: "dispenser",
        ope: this.operation.id,
        selfWalletConnexion: this.operation.dispenser?.selfWalletConnection,
        mining: this.operation.lazy_mining
      });
    return null;
  }

  send(nft: any) {
    if(nft.quantity==0){
      showMessage(this,"Ce NFT ne peut plus être miné");
      return;
    }

    nft.price=0;
    if(this.operation){
      this.router.navigate(["dm"],{queryParams:{param:this.get_nft_link(nft)}})
    }


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

  copy_link(nft: NFT) {
    let url=this.get_nft_link(nft);
    if(url){
      url=environment.appli+"/dm?param="+url;
      this.clipboardService.copy(url);
      showMessage(this,"Le lien de distribution est dans votre presse-papier")
    }

  }

    get_all_nfts(field_separator="\t",line_separator="\n") {
        let rc:string="Address;Name;Collection;Destinataire"+line_separator;
        for(let nft of this.nfts){
          rc=rc+nft.address+";"+nft.name+";"+nft.collection?.id+line_separator;
        }
        rc=rc.replace(/\;/gi,field_separator)
        this.clipboardService.copy(rc);
        showMessage(this,"L'ensemble des NFTs sont dans votre presse-papier. Vous pouvez utiliser un fichier excel pour les envoyer en masse")
    }

  on_upload($event: any) {
    debugger
  }
}
