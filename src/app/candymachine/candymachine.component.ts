import { Component, OnInit } from '@angular/core';
import {$$, find_miner_from_operation, getParams, isEmail, showError, showMessage} from "../../tools";
import {Collection, Operation} from "../../operation";
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

  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
    public dialog:MatDialog,
    public _location:Location,
    public network: NetworkService
  ) { }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
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
      },(err:any)=>{
        showError(this,err);
      })
    }).catch(()=>{
      debugger
    })
  }


  authent($event:any) {
    if(this.operation?.network){
      this.is_email=isEmail($event.address);

      let target=find_miner_from_operation(this.operation,$event.address);
      let body={
        dest:$event.address,
        sources: this.operation.data.sources,
        target: target,
        network: this.operation.network,
        miner: target.miner,
        operation:this.operation,
        collections:target.collection,
        wallet:environment.wallet
      }
      $$("Ajout de la demande de minage ",body)
      this.network.add_user_for_nft(body).subscribe(()=>{
        this.showEnd=true;
      })
    }
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
