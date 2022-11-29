import { Component, OnInit } from '@angular/core';
import {$$, getParams, showError, showMessage} from "../../tools";
import {Collection, Operation} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {environment} from "../../environments/environment";
import {_prompt} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";

@Component({
  selector: 'app-candymachine',
  templateUrl: './candymachine.component.html',
  styleUrls: ['./candymachine.component.css']
})
export class CandymachineComponent implements OnInit {
  operation: Operation | null=null;
  showEnd: boolean=false;
  collections: Collection[]=[];
  miner="";
  is_email=false;
  airdrop: boolean=false;
  addresses="";
  _style={};
  title="";

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
        if(this.operation?.branding)this._style=this.operation.branding.style;
        if(this.operation?.candymachine.messages.title)this.title=this.operation.candymachine.messages.title;
        this.miner=(params.hasOwnProperty('miner') ? params["miner"] : operation.lazy_mining.miner)
        $$("Le miner de la transaction est "+this.miner);
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
      this.is_email=$event.address.indexOf("@")>-1;
      let body={
        owner:$event.address,
        network:this.operation?.network,
        miner: this.miner,
        operation:this.operation,
        collections:this.operation.candymachine.collections,
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
      let body={
        owner:l_addresses,
        network:this.operation?.network,
        miner: this.miner,
        operation:this.operation,
        collections:this.operation!.airdrop!.collections,
        wallet:environment.wallet
      }

      this.network.add_user_for_nft(body).subscribe(()=>{
        showMessage(this,"L'ensemble des destinataires vont recevoir progressivement les NFTs")
        this.back();
      })

    });
  }
}
