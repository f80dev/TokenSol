import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";
import {getParams, showMessage} from "../../tools";
import {Operation} from "../../operation";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-autovalidate',
  templateUrl: './autovalidate.component.html',
  styleUrls: ['./autovalidate.component.css']
})
export class AutovalidateComponent implements OnInit {
  operation: Operation | null=null;
  message: string | undefined ="";

  constructor(
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.network.get_operations(params["ope"]).subscribe((ope)=>{
        this.operation=ope;
      })
    })
  }

  on_authent($event: { address:string,strong:boolean,nftchecked:boolean}) {
    if($event.strong){
      this.message=this.operation?.validate?.actions.success.message;
      let url=this.operation?.validate?.actions.success.redirect;
      if(url && url.length>0)open(url);
    } else {
      this.message=this.operation?.validate?.actions.fault.message;
      let url=this.operation?.validate?.actions.fault.redirect;
      if(url && url.length>0)open(url);
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
}
