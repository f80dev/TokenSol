import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";
import {Token} from "../nfts/nfts.component";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {getExplorer, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {SALT} from "../../definitions";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  operation_name: string ="calvi2022";
  query: string="";
  tokens:Token[]=[];
  message="";
  operation: any={};
  attributes_to_show: any[]=[];
  user: string = "";
  access_code: string="";
  result_message: string = "";
  email: string="";
  last_action: any={};

  constructor(public routes:ActivatedRoute,
              public network:NetworkService,
              public _location:Location,
              public toast:MatSnackBar,
              public alias:AliasPipe
  ) { }



  ngOnInit(): void {
    this.operation_name=this.routes.snapshot.queryParamMap.get("operation") || this.routes.snapshot.queryParamMap.get("ope") || "";
    this.query=this.routes.snapshot.queryParamMap.get("q") || "";
    this.user=this.routes.snapshot.queryParamMap.get("user") || "";
    this.access_code=this.routes.snapshot.queryParamMap.get("access_code") || "";
    if(this.operation_name=="")this._location.back();
    this.network.get_operations(this.operation_name).subscribe((ope:any)=>{
      this.operation=ope[0].content;
      setTimeout(()=>{this.update_token(this.query);},1500);
    })
  }

  search(query:string){
    this.network.isValideToken("calvi2022",query).subscribe((r:any)=>{})
  }

  update_model($event:any) {
    if($event.keyCode==13)
      this.update_token(this.query);
  }

  update_token(address:string){
    if(address.length==0 || this.operation.validate==null)return;
    let addr=this.alias.transform(address,"pubkey");
    this.message="Recherche des NFTs";

    //let filter={mintAuthority:this.alias.transform(this.operation.validate.filter.mintAuthority,"pubkey")};
    let filters=this.operation.validate.filters;

    this.network.get_tokens_from("owner",addr,200,false).then((r:any[])=>{
      this._location.replaceState("./validate/?q="+this.query+"&ope="+this.operation_name);
      for(let t of r){

        if(t.metadataOffchain){
          //Application des filtres
          let filter_Ok=false;
          if(filters.name){
            for(let filter_name of filters.name){
              if(t.metadataOffchain.name.indexOf(filter_name)>-1){
                filter_Ok=true;
                break;
              }
            }
          }

          if(filter_Ok){
            let prop=t.metadataOffchain.attributes;
            let indexes=[]
            for(var index=0;index<prop.length;index++){
              if(this.operation.validate.properties.indexOf(prop[index]["trait_type"])>-1)
                indexes.push(index)
            }
            if(indexes.length>0){
              this.tokens.push(t);
              this.attributes_to_show.push(indexes)
            }
            this.message="";
          }
        }


      }
    },(err)=>{
      this.message="";
      showError(this,err);
    })
  }

  onflash($event: any) {
    let addr=$event;
    this.update_token(addr);
  }

  validate(t:Token,action:any) {
    this.last_action={action:action,token:t};
    this.message="Validation en cours";
    this.network.validate(action,t,this.query,this.access_code).subscribe((traitement:any)=>{
      showMessage(this,traitement.message);
      this.result_message=traitement.message;
      this.message="";
      this.tokens=[];
      this.query="";
      this._location.replaceState("./validate?ope="+this.operation_name)
    },(err)=>{
      showError(this,"Incident. Veuillez recommencer l'opération");
    })
  }

  update_access_code() {
    let pos=this.operation.validate.access_codes.indexOf(this.access_code)
    if(this.access_code=="4271"){
      pos=this.operation.validate.users.indexOf("hhoareau@gmail.com");
    }
    if(pos>-1){
      this.user=this.operation.validate.users[pos]
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
}
