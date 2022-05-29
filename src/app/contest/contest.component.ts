import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-contest',
  templateUrl: './contest.component.html',
  styleUrls: ['./contest.component.css']
})
//test: http://127.0.0.1:4200/contest?ope=demo
export class ContestComponent implements OnInit {

  ope:string="";
  qrcode: string="";
  url: string="";
  visual: string="";

  constructor(
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }

  ask_token(ope:string){
    if(ope!=''){
      this.network.get_new_token(ope,environment.appli).subscribe((r:any)=>{
        this.qrcode=r.qrcode;
        this.url=r.url;
        this.visual=r.visual || "";
      },(err:any)=>{
        if(err.status!=404)
          showMessage(this,"Opération non référencée");
      });
    }
  }

  ngOnInit(): void {
    this.ope=this.routes.snapshot.queryParamMap.get("ope") || "";
    this.ask_token(this.ope!);
    if(this.ope && this.ope!=''){
      setInterval(()=>{this.ask_token(this.ope!)},Number(this.routes.snapshot.queryParamMap.get("delay")) || 3000);
    }

  }

}
