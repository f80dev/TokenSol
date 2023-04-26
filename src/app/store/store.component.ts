import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {getParams, setParams, showMessage} from "../../tools";
import {NFT} from "../../nft";
import {get_in, Operation} from "../../operation";


@Component({
  selector: 'app-store',
  templateUrl: './store.component.html',
  styleUrls: ['./store.component.css']
})
export class StoreComponent implements OnInit {
  operation: Operation | undefined;
  nfts: NFT[]=[];
  message: string="";
  title:string="";
  subtitle:string="";
  bgcolor: string="white";
  style_reverse_card={padding:'5%',width: '90%',height:'90%',position: 'relative'};
  fontsize: number=12;

  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.bgcolor=params.bgcolor || "white";

      this.network.get_operations(params.ope).subscribe((ope:Operation)=> {
        this.operation = ope;
        if(this.operation){
          this.title=params.title || ope.store?.messages.title;
          this.subtitle=get_in(ope,"store.messages.subtitle","");
          this.fontsize=get_in(ope,"store.apparence.fontsize",20);

          if(this.operation.branding.reverse_card)this.style_reverse_card={...this.style_reverse_card,...this.operation.branding.reverse_card}

          this.message="Chargement des NFTs";
          this.network.get_tokens_to_send(ope.id,"store",50).subscribe((nfts:any) => {
            this.nfts=[];
            for(let nft of nfts){
              nft.price=0;
              nft.supply=1;
              if(this.operation?.store)
                for(let c of this.operation.store.collections || []){
                  if(c.name==nft.collection){
                    nft.price=c.price
                    nft.supply=nft.supply
                  }
                }
              this.nfts.push(nft);
            }
            this.message="";
          });
        }
      },(err)=>{
        showMessage(this,"Operation impossible à charger");
      })
    })

  }

  buy(nft: NFT) {
    if(this.operation && this.operation.store && this.operation.mining){
      let param=setParams({
        token:nft,
        ope:this.operation.id,
        selfWalletConnexion:true,
        mining:this.operation.mining?.networks[0].miner,
        section:"store"
      },"","")
      this.router.navigate(["dm"],{queryParams:{p:param}});
    }
  }
}
