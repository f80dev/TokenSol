import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {apply_params, getParams, setParams, showMessage} from "../../tools";
import {NFT} from "../../nft";
import {get_in, Operation} from "../../operation";
import {environment} from "../../environments/environment";
import {StyleManagerService} from "../style-manager.service";
import {wait_message} from "../hourglass/hourglass.component";
import {Merchant} from "../payment/payment.component";


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
  fontsize: number=12
  default_price: any
  address:string=""
  merchant:Merchant={contact: "", country: "fr", currency: "eur", id: "", name: "", wallet: undefined}
  miner: any;

  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public style:StyleManagerService,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }

  async ngOnInit() {
    try{
      let params:any=await getParams(this.routes);
      apply_params(this,params,environment)
      if(params.default_price)this.default_price=params.default_price;
      this.address=params.miner_addr

      wait_message(this,"Chargement des NFTs")
      if(params.ope){
        this.network.get_operations(params.ope).subscribe((ope:Operation)=> {
          this.operation = ope;
          this.miner=this.operation.mining?.networks[0].miner
          if(this.operation){
            this.title=params.title || ope.store?.messages.title;
            this.subtitle=get_in(ope,"store.messages.subtitle","");
            this.fontsize=get_in(ope,"store.apparence.fontsize",20);

            if(this.operation.branding.reverse_card)this.style_reverse_card={...this.style_reverse_card,...this.operation.branding.reverse_card}

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
      }else{
          this.miner=params.miner;
          this.merchant=params.merchant;
          if(params.collection){
            this.network.get_nfts_from_collection(params.collection,params.network).subscribe(result=>{
              this.nfts=this.eval_nfts(result.nfts)
              wait_message(this)
            })
          }else{
            let resp=await this.network.get_tokens_from("owner",params.miner_addr,100,false,null,0,params.network)
            this.nfts=this.eval_nfts(resp.result)
            wait_message(this)
          }
      }
    } catch (e) {

    }

  }

  buy(nft: NFT) {
    let ope= this.operation ? this.operation.id : ""
      let param=setParams({
        token:nft,
        ope:ope,
        merchant:this.merchant,
        selfWalletConnexion:true,
        mining:this.miner,
        section:"store",
        toolbar:false,
        miner_dest:this.miner,
        collection_dest:nft.collection!.id,
        network_dest:nft.network
      },"","")
      this.router.navigate(["dm"],{queryParams:{p:param}});

  }

  eval_nfts(nfts: NFT[]) {
    let rc:NFT[]=[]
    for(let nft of nfts){
      if(!nft.price && this.default_price)nft.price=this.default_price;
      rc.push(nft)
    }
    return rc
  }

  show_price(nft:NFT): string {
    let price=nft.price
    if(!price)return("Acquérir")
    return "Acheter "+Object.values(price)[0]+" "+Object.keys(price)[0]
  }
}
