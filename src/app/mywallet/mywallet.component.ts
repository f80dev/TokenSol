import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {getParams, removeBigInt, showError, showMessage} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NFT} from "../nfts/nfts.component";


//Test : http://localhost:4200/wallet?addr=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr&toolbar=false
@Component({
  selector: 'app-mywallet',
  templateUrl: './mywallet.component.html',
  styleUrls: ['./mywallet.component.css']
})
export class MywalletComponent implements OnInit {
  nfts: NFT[]=[];
  indexTab: number=0;
  addr:any="";
  url_key: any="";
  showDetail=false;

  constructor(public user:UserService,
              public routes:ActivatedRoute,
              public toast:MatSnackBar,
              public network:NetworkService) { }


  ngOnInit(): void {
    this.addr=getParams(this.routes,"addr")
    if(!this.addr)showMessage(this,"Adresse non disponible, vous pouvez fermer cette fenêtre");
    this.showDetail=getParams(this.routes,"show_detail",false);
    this.network.network=getParams(this.routes,"network",this.addr.startsWith("erd") ? "elrond-devnet" : "solana-devnet");
    this.url_key=environment.server+"/api/key/"+this.addr+"?format=qrcode";
    this.refresh();
  }

  refresh(index:number=0) {
    if(index==0 && this.nfts.length==0){
      this.network.wait("Chargement de vos NFTs");
      for(let arg of [[0,2],[2,6],[6,10],[10,1000]]){
        let offset=arg[0];
        let limit=arg[1];
        setTimeout(()=>{
          this.network.get_tokens_from("owner",this.addr,limit,false,null,offset).then((r:NFT[])=>{

            for(let nft of r){
              if(nft.visual)
                this.nfts.push(nft);
            }
            if(r.length==0) {
              if (arg[0] == 0)
                showMessage(this, "Vous n'avez aucun NFT pour l'instant")
              else
                this.network.wait("");

            }

          }).catch(err=>{showError(this,err)});
        },offset*500);
      }
    }
  }
}
