import {Component, OnDestroy, OnInit} from '@angular/core';
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
export class ContestComponent implements OnInit,OnDestroy {

  operation:any;
  qrcode: string="";
  url: string="";
  visual: string="";
  delay=0;
  handle: any;

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
    this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((ope:any)=>{
      this.operation=ope;
      this.handle=setInterval(()=>{
        if(this.delay==0){
          this.delay=this.operation.lottery.duration;
          this.ask_token(this.operation.id!)
        }
        this.delay=this.delay-1;
        },1000);
    })
  }

  ngOnDestroy(): void {
    clearInterval(this.handle);
  }

}
