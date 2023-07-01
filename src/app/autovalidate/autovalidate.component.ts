import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";
import {getParams, showMessage} from "../../tools";
import {Connexion, Operation} from "../../operation";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-autovalidate',
  templateUrl: './autovalidate.component.html',
  styleUrls: ['./autovalidate.component.css']
})
export class AutovalidateComponent implements OnInit {
  operation: Operation | null=null;
  message: string | undefined ="";
  validator_name: any;
  authentification: Connexion | undefined;
  collections:string[]=[];
  network_name="";

  constructor(
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.validator_name=params["validator_name"]
      this.authentification=params["authentification"] || {wallet_connect:true,nfluent_wallet_connect:true,extension_wallet:true};
      this.network_name=params["network"]
      if(params.hasOwnProperty("collections")){
        this.collections=params["collections"];
        if(typeof params["collections"]=="string")this.collections=params["collections"].split(",");
      }else{
        this.collections=[params["collection"]];
      }
      //if(params.hasOwnProperty("ope"))this.network.get_operations(params["ope"]).subscribe((ope)=>{this.operation=ope;})
    })
  }


  on_authent($event: { address:string,strong:boolean}) {
    if($event.strong){
      this.message=this.operation?.validate?.actions.success.message;
    } else {
      this.message=this.operation?.validate?.actions.fault.message;
    }
    setTimeout(()=>{this.message=""},2000);
    showMessage(this,this.message);
  }

  on_disconnect() {
    this.message="";
  }

  on_invalid() {
    showMessage(this,"NFT requis pour l'accès non présents")
  }

  success(addr:string) {
    showMessage(this,"L'utilisateur  "+addr+" possède bien le NFT requis")
  }

  fail(addr:string){
    showMessage(this,"L'utilisateur "+addr+" ne possède pas le NFT requis")
  }
}
