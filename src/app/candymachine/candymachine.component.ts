import { Component, OnInit } from '@angular/core';
import {$$, find_miner_from_operation, getParams, isEmail, showError, showMessage} from "../../tools";
import {Collection, Connexion, Operation, Source} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {environment} from "../../environments/environment";
import {_prompt} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {NFT} from "../../nft";

@Component({
  selector: 'app-candymachine',
  templateUrl: './candymachine.component.html',
  styleUrls: ['./candymachine.component.css']
})
export class CandymachineComponent implements OnInit {
  operation: Operation | null=null;
  showEnd: boolean=false;
  collections: Collection[]=[];
  is_email=false;
  airdrop: boolean=false;
  addresses="";
  _style={};
  title="";
  nfts: NFT[]=[]
  params: any={}
  connexion: Connexion | undefined;

  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
    public dialog:MatDialog,
    public _location:Location,
    public network: NetworkService
  ) { }


  async ngOnInit() {
    let params:any=await getParams(this.routes)
    if(params.ope){
      this.network.get_operations(params["ope"]).subscribe((operation:any)=>{
        this.airdrop=params.hasOwnProperty('airdrop') ? params["airdrop"] : false;
        this.operation=operation;

        this.network.get_nfts_from_operation(operation.id).subscribe((result)=>{
          this.nfts=result.nfts;
        })

        if(this.operation?.branding)this._style=this.operation.branding.style;
        if(this.operation?.candymachine.messages.title)this.title=this.operation.candymachine.messages.title;
        // this.miner=(params.hasOwnProperty('miner') ? params["miner"] : operation.mining.miner)

        if(operation.collections){
          for(let col of operation.collections){
            if(((operation.candymachine.collections.length==0 || operation.candymachine.collections.indexOf(col.id)>-1) && !this.airdrop)
                || ((operation.airdrop.collections.length==0 || operation.airdrop.collections.indexOf(col.id)>-1) && this.airdrop)){
              this.collections.push(col);
            }
          }
        }
      })
    }else{
      this.params=params;
      this.connexion={
        direct_connect: false, extension_wallet: false, web_wallet: false,
        address: false,
        email: true,
        google: true,
        nfluent_wallet_connect: true,
        on_device: false,
        wallet_connect: true,
        webcam: false
      }
      this.network.get_nfts_from_collection(params.collection,params.network).subscribe((result)=>{this.nfts=result.nfts})
       //this.network.get_collections(params.collection,params.network,false).subscribe((cols)=>{this.collections=cols;})
    }
  }


  authent($event:any) {
    this.is_email=isEmail($event.address);
    let body={}
    if(this.operation && this.operation?.network){
      let target=find_miner_from_operation(this.operation,$event.address);
      body={
        dest:$event.address,
        sources: this.operation.data.sources,
        target: target,
        network: this.operation.network,
        miner: target.miner,
        operation:this.operation,
        collections:target.collection,
        wallet:environment.wallet
      }
    }else {
      let source: Source = {
        active: true,
        collections: [this.params.collection],
        connexion: this.params.network,
        dbname: "",
        filter: undefined,
        miner: this.params.miner,
        type: "network"
      }
      let target = {
        miner: this.params.miner_dest,
        collection: this.params.collection_dest,
        network: this.params.network_dest
      }
      body = {
        dest: $event.address,
        sources: [source],
        target: target,
        miner: target.miner,
        collections: target.collection,
        wallet: environment.wallet
      }
    }
    $$("Ajout de la demande de minage ",body)
    this.network.add_user_for_nft(body).subscribe(()=>{this.showEnd=true;})
  }

  back() {
    this._location.back();
  }

  invalid() {
    showMessage(this,"Connexion non valide");
  }

  start_airdrop() {
    let l_addresses=this.addresses.split("\n");
    _prompt(this,"Envoyer des NFTs de la collection à "+l_addresses.length+" personnes ?","","","text","ok","Annuler",true).then(()=>{
      let target=find_miner_from_operation(this.operation,l_addresses[0])
      let body={
        owner:l_addresses,
        network:target.network,
        miner: target.miner,
        operation:this.operation,
        collections:target.collection,
        wallet:environment.wallet
      }

      this.network.add_user_for_nft(body).subscribe(()=>{
        showMessage(this,"L'ensemble des destinataires vont recevoir progressivement les NFTs")
        this.back();
      })

    });
  }
}
