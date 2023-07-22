import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute, Router} from "@angular/router";
import {
  $$,
  apply_params,
  canTransfer,
  CryptoKey,
  getParams,
  newCryptoKey,
  setParams,
  showError,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {MatDialog} from "@angular/material/dialog";

import {Collection, Connexion, newCollection, Operation} from "../../operation";
import {NFT} from "../../nft";
import {Clipboard} from "@angular/cdk/clipboard";
import {environment} from "../../environments/environment";
import {UserService} from "../user.service";
import {_prompt} from "../prompt/prompt.component";
import {genlink_to_obj} from "../genlink/genlink.component";
import {StyleManagerService} from "../style-manager.service";
import {NgNavigatorShareService} from "ng-navigator-share";

@Component({
  selector: 'app-dispenser',
  templateUrl: './dispenser.component.html',
  styleUrls: ['./dispenser.component.css']
})
export class DispenserComponent implements OnInit {
  nfts: NFT[]=[];
  message="";
  operation: Operation | undefined;
  dest=""; //Destinataire
  miner:CryptoKey | undefined;
  miner_addr:string=""
  miner_dest: CryptoKey | undefined;
  network_dest: string="";

  collections: Collection[]=[];
  appli=environment.appli;
  dm_props:any[]=[];

  collection_dest:Collection | undefined;

  constructor(
      public network:NetworkService,
      public routes:ActivatedRoute,
      public dialog:MatDialog,
      public share:NgNavigatorShareService,
      public router:Router,
      public user:UserService,
      public toast:MatSnackBar,
      public alias:AliasPipe,
      public style:StyleManagerService,
      public clipboardService:Clipboard
  ) {}

  eval_nfts(nfts:NFT[],collections:string[]){
    for(let nft of nfts){
      if(canTransfer(nft,this.miner_addr)){
        nft.style={opacity:1};
      } else {
        nft.style={opacity:0.3,cursor:"not-allowed",pointerEvents:"none"};
        nft.message="Déjà distribué"
      }
      nft.message=nft.owner+" - "+nft.address;
      if(!nft.hasOwnProperty("price"))nft.price=0;

      $$("Evaluation de la possibilité d'ajouté le NFT");

      let canAdd=nft.address ? nft.address.startsWith("db_") || nft.address.startsWith("file_") : false;
      if(!canAdd)canAdd=(nft.price==0 && nft.owner==nft.creators[0].address);
      if(canAdd)canAdd=(collections.indexOf(nft.collection!.id)>-1)
      if(canAdd)this.nfts.push(nft);
    }
  }

  //test: http://127.0.0.1:4200/dispenser?ope=calvi22_devnet&toolbar=false/dispenser?ope=calvi22_devnet
  background: string="";
  title=""
  claim="";

  refresh(){
    this.network.get_nfts_from_collection(this.user.params.collection,this.user.params.network).subscribe(result=>{
      this.eval_nfts(result.nfts,[this.user.params.collection])
      this.message="";
    })
  }

  async ngOnInit() {
    let params:any=await getParams(this.routes)
    apply_params(this,params);
    this.user.params=params;
    let limit=Number(params["limit"] || "1000") ;
    this.message="Préparation de la page";
    this.nfts=[];

    this.miner_addr=params.miner_addr;
    if(params.ope){
      this.network.get_operations(params["ope"]).subscribe((operation:Operation)=>{
        this.operation=operation;
        //this.miner=operation.mining?.networks[0].miner;
        this.message="Chargement des NFTs";
        this.network.get_tokens_to_send(operation.id,"dispenser",limit).subscribe((nfts:any) => {

          this.message="";
          if(operation.dispenser){
            this.eval_nfts(nfts,operation.dispenser.collections)

          }
        });
      })
    }else{
      debugger
      this.network.network=params.network
      this.miner=newCryptoKey(params.miner_addr,"","",params.miner)
      this.network_dest=params.network_dest
      this.miner_dest=newCryptoKey("","","",params.miner_dest)
      this.collection_dest=newCollection("",this.miner_dest,params.collection_dest)
      this.dm_props=[
          {label: "Réseau",value:this.network_dest,name:"network_dest"},
              {label: "Collection",value:this.collection_dest!.id,name:"collection_dest"},
              {label: "Miner",value:this.miner_dest!.encrypt,name:"miner_dest"},

              {label: "Style",value:"nfluent.css",name:"style"},
              {label: "Nom de l'application",value:"Mineur de NFT",name:"appname"},
              {label: "Fond d'écran",value:"https://s.f80.fr/assets/wood.jpg",name:"background"},
              {label: "FavIcon",value:"favicon.png",name:"favicon"}
          ];

      this.update_miner_dest()
      this.refresh();
    }
  }

  update_miner_dest(){
    if(this.miner_dest && this.network_dest!=''){
      this.network.get_collections(this.miner_dest.address,this.network_dest,false).subscribe((cols)=>{
        this.collections=cols;
      })
    }
  }


  get_nft_link(nft:any){
    if(this.operation){
      return setParams({
        token: nft,
        price: 0,
        section: "dispenser",
        ope: this.operation.id,
        selfWalletConnexion: this.operation.dispenser?.selfWalletConnection,
        mining: this.operation.mining
      },"","");
    }
    else{
      let c:Connexion={
        keystore: false,
        address: false,
        direct_connect: false,
        email: true,
        extension_wallet: true,
        google: false,
        nfluent_wallet_connect: true,
        on_device: false,
        wallet_connect: true,
        web_wallet: false,
        webcam: true
      }
      let obj=genlink_to_obj(this.dm_props);
      obj.nft=nft;
      obj.miner=this.miner?.encrypt
      obj.price=0
      obj.authentification=c;
      obj.toolbar=false;

      return setParams(obj,"","");
    }
  }

  async send(nft: any) {
    //Envoi du NFT

    if(nft.balances[this.miner!.address]==0){
      showMessage(this,"Ce NFT ne peut plus être miné");
      return;
    }

    nft.price=0;
    // if(this.operation){
    //   this.router.navigate(["dm"],{queryParams:{p:this.get_nft_link(nft)}})
    // }

    if(!this.dest)this.dest=await _prompt(this,"Destinataire","","une adresse de wallet ou email","text","Envoyer","Annuler",false)

    if(this.dest && this.miner && this.miner_dest && this.collection_dest){
      this.message="Minage et envoi en cours sur le wallet "+this.dest;
      this.network.transfer_to(nft.address, this.dest,this.miner,this.miner_dest,this.network.network,this.network_dest,this.collection_dest.id).subscribe((r:any)=>{
        this.message="";
        showMessage(this,"Envoyé");
        this.refresh();
      },(err:any)=>{
        showError(this,err);
      });
    }else{
      showMessage(this,"Envoi annulé");
    }

  }

  copy_link(nft: NFT) {
    let url=this.get_nft_link(nft);
    if(url){
      url=environment.appli+"/dm?p="+url;
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

    share_url() {
        this.share.share({
          title:this.user.params.appname,
          text:this.user.params.claim,
          url:this.router.url
        })
    }
}
