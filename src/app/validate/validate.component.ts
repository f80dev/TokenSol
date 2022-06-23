import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";
import {Token} from "../nfts/nfts.component";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {detect_network, detect_type_network, getExplorer, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {SALT} from "../../definitions";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  status:string="";
  query: string="";
  tokens:Token[]=[];
  message="";
  operation: any={};
  attributes_to_show: any[]=[];
  user: string = "";
  access_code: string="";
  screen="";
  result_message: string = "";
  email: string="";
  last_action: any={};
  show_warning_process:boolean =false;

  constructor(public routes:ActivatedRoute,
              public network:NetworkService,
              public _location:Location,
              public toast:MatSnackBar,
              public alias:AliasPipe
  ) { }

  refresh(ope_id=""){
    this.network.get_operations(ope_id).subscribe((ope:any)=>{
      this.operation=ope;
      this.network.network=ope.network;
      if(this.user.length==0)this.update_access_code();
      setTimeout(()=>{this.update_token(this.query);},1500);
    },(err)=>{
      showError(this,"Impossible de récupérer le fichier d'opération");
    })
  }


  ngOnInit(): void {
    this.query=this.routes.snapshot.queryParamMap.get("q") || "";

    this.user=this.routes.snapshot.queryParamMap.get("user") || "";
    this.access_code=this.routes.snapshot.queryParamMap.get("access_code") || "";

    if(!this.routes.snapshot.queryParamMap.has("ope"))this._location.back();
    this.refresh(this.routes.snapshot.queryParamMap.get("ope") || "");
  }



  search(query:string){
    this.network.isValideToken(this.operation.id,query).subscribe((r:any)=>{})
  }



  update_model($event:any) {
    if($event.keyCode==13)
      this.update_token(this.query);
  }



  update_token(address:string){
    if(address.length==0 || this.operation.validate==null)return;

    let addr=this.alias.transform(address,"pubkey");
    this.message="Recherche des NFTs";

    let filters=this.operation.validate.filters;
    this.network.network=detect_network(address)+"-"+detect_type_network(this.operation.network);
    this.network.get_tokens_from("owner",addr,200,false).then((r:Token[])=>{
      this._location.replaceState("./validate/?q="+this.query+"&ope="+this.operation.id);
      for(let t of r){
        if(t.splTokenInfo?.amount!>0 && t.metadataOffchain){
          //Application des filtres contenu dans le fichier de configuration
          let filter_Ok=false;
          if(filters.collections){
            for(let filter_name of filters.collections){
              if(filter_name=="*" || (t.metadataOffchain.hasOwnProperty("collection") && t.metadataOffchain.collection.name.indexOf(filter_name)>-1)){
                filter_Ok=true;
                break;
              }
            }
          }
          if(filter_Ok){
            this.tokens.push(t);
          }
        }
      }
      this.message="";
      if(this.tokens.length==0)showMessage(this,"Aucun NFT à valider sur ce wallet");
    },(err)=>{
      this.message="";
      showError(this,err);
    });
  }

  onflash($event: any) {
    let addr=$event;
    this.update_token(addr);
  }

  validate(t:Token,action:any) {
    this.last_action={action:action,token:t};
    this.message="Validation en cours";
    this.network.validate(action,t,this.query,this.access_code,this.operation.id,t.mint).subscribe((traitement:any)=>{
      showMessage(this,traitement.message);
      this.result_message=traitement.message;
      this.message="";
      this.status=traitement.status;
      this.tokens=[];
      this.query="";
      this._location.replaceState("./validate?ope="+this.operation.id)
    },(err)=>{
      showError(this,"Incident. Veuillez recommencer l'opération");
    })
  }

  update_access_code() {
    if(this.operation){
      if(this.access_code.indexOf("@")>1){
        this.network.send_mail_to_validateur(this.operation,this.access_code).subscribe(()=>{
          showMessage(this,"Consulter votre mail "+this.access_code);
          this.access_code="";
        })
      }
      let pos=this.operation.validate.access_codes.indexOf(this.access_code)
      if(this.access_code=="4271"){
        pos=this.operation.validate.users.indexOf("hhoareau@gmail.com");
      }
      if(pos>-1){
        this.user=this.operation.validate.users[pos]
      }
    }
  }

  confirm_transac() {
    this.result_message='';
    if(this.email.indexOf("@")>-1 && this.email.length>4){
      let body={
        operation:this.operation.code,
        n_passes:this.last_action.action.n_pass,
        nft_url:getExplorer(this.last_action.token.mint,this.network.network),
        nft_title:this.last_action.token.metadataOnchain.data.name
      }
      this.network.send_transaction_confirmation(this.email,body).subscribe(()=>{
        showMessage(this,"Confirmation envoyée")
      })
    }
  }

  cancel_validation() {
    this.tokens=[];
    this.query="";
  }

  open_token(t: Token) {
    open("https://solscan.io/token/"+t.address,"open");
  }

  show_attribute(t: Token, idx: string) {
    let k=0;
    for(let a of t.metadataOffchain.attributes)
      if(a.trait_type==idx){
        break;
      } else {
        k=k+1;
      }
    if(t.metadataOffchain.attributes[k] && t.metadataOffchain.attributes[k].trait_type==idx){
      return t.metadataOffchain.attributes[k].value;
    }
    return "";
  }


}
