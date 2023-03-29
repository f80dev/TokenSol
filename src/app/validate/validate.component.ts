import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";

import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {detect_network, detect_type_network,  getParams, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Operation} from "../../operation";
import {NFT} from "../../nft";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  status:string="";
  query: string="";
  tokens:NFT[]=[];
  message="";
  operation: Operation | null=null;
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
    getParams(this.routes).then((params:any)=>{
      this.query=params["q"] || "";
      this.user=params["user"] || "";
      this.access_code=params["access_code"] || "";
      if(!params.hasOwnProperty("ope"))this._location.back();
      this.refresh(params["ope"]);
    })
  }



  search(query:string){
    this.network.isValideToken(this.operation!.id,query).subscribe((r:any)=>{})
  }



  update_model($event:any) {
    if($event.keyCode==13)
      this.update_token(this.query);
  }


  check_addr(access_code:any){
    if(access_code.keyCode==13){
      if(detect_network(this.query)!="access_code"){
        this.update_token(this.query)
      } else {
        this.network.check_access_code(this.query).subscribe((result:any)=>{
          this.update_token(result.address)
        },(err:any)=>{
          showMessage(this,"Ce code est incorrect",6000);
          this.query="";
        })
      }
    }
  }


  update_token(address:string){
    if(address.length==0 || this.operation!.validate==null)return;

    let addr=this.alias.transform(address,"address");
    this.message="Recherche des NFTs";

    let filters=this.operation!.validate.filters;

    let network=detect_network(address)+"-"+detect_type_network(this.operation!.network);
    this.network.get_tokens_from("owner",addr,10,false,network).then((r:any)=>{
      if(this.message.length>0){
        for(let t of r.result){
          if(t.balances[address]>0){
            //Application des filtres contenu dans le fichier de configuration
            let filter_Ok=false;
            if(filters.collections){
              for(let filter_name of filters.collections){
                if(filter_name=="*" || (t.hasOwnProperty("collection") && t.collection!.id!.indexOf(filter_name)>-1)){
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
      }
      if(this.tokens.length==0)showMessage(this,"Aucun NFT à valider sur ce wallet");
    },(err)=>{
      this.message="";
      showError(this,err);
    });
  }

  onflash($event: any) {
    let addr=$event.data;
    this.query=addr
    this.check_addr({keyCode:13});
  }

  validate(t:NFT,action:any) {
    this.last_action={action:action,token:t};
    this.message="Validation en cours";
    this.network.validate(action,t,this.query,this.access_code,this.operation!.id).subscribe((traitement:any)=>{
      showMessage(this,traitement.message);
      this.result_message=traitement.message;
      this.message="";
      this.status=traitement.status;
      this.tokens=[];
      this.query="";
      this._location.replaceState("./validate?ope="+this.operation!.id)
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
    }
  }

  confirm_transac() {
    this.result_message='';
    if(this.email.indexOf("@")>-1 && this.email.length>4){
      let body={
        operation:this.operation!.id,
        n_passes:this.last_action.action.n_pass,
        nft_url:this.network.getExplorer(this.last_action.token.mint),
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

  open_token(t: NFT) {
    open("https://solscan.io/token/"+t.address,"open");
  }

  show_attribute(t: NFT, idx: string) {
    let k=0;
    for(let a of t.attributes)
      if(a.trait_type==idx){
        break;
      } else {
        k=k+1;
      }
    if(t.attributes[k] && t.attributes[k].trait_type==idx){
      return t.attributes[k].value;
    }
    return "";
  }


}
