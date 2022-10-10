import {Component, OnDestroy, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {$$, getParams, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Operation} from "../../operation";
import {NFT} from "../../nft";

@Component({
  selector: 'app-contest',
  templateUrl: './contest.component.html',
  styleUrls: ['./contest.component.css']
})
//test: http://127.0.0.1:4200/contest?ope=demo
export class ContestComponent implements OnInit,OnDestroy {

  operation:Operation | null=null;
  qrcode: string="";
  url: string="";
  visual: string="";
  delay=0;
  handle: any;
  minutes: string="0";
  secondes: number=0;
  nft_address: string="";

  constructor(
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public network:NetworkService
  ) { }


  ask_token(){
   if(this.operation)
      this.network.get_new_token(this.operation.id,environment.appli).subscribe((r:any)=>{
        this.qrcode=r.qrcode;
        this.url=r.url;
        this.visual=r.visual || "";
        this.nft_address=r.address;
      },(err:any)=>{
        if(err.status!=404)
          showMessage(this,"Opération non référencée");
      });
  }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      let ope=params["ope"];
      this.network.get_operations(ope).subscribe((ope:any)=>{
        this.operation=ope;

        this.handle=setInterval(()=>{
          if(this.delay==0 && this.operation){
            this.delay=this.operation.lottery.duration;
            this.ask_token()
          }
          this.delay=this.delay-1;
          let minutes=Math.trunc(this.delay/60);
          this.minutes=(minutes<10 ? "0" : "")+minutes;
          this.secondes=this.delay % 60;
        },1000);
      },(err:any)=>{
        showError(this,err);
      })
    })
  }




  ngOnDestroy(): void {
    clearInterval(this.handle);
  }


  on_authent(evt:{address:string}) {
    $$("Récupération de l'adresse "+evt.address);
    if(this.operation && this.operation.lottery && this.nft_address.length>0){
      this.network.mint_for_contest(
        evt.address,
        this.operation?.id,
        this.operation.lottery.miner || "",
        "ipfs",
        this.operation?.network,
        null,
        this.nft_address
      ).subscribe(()=>{
        this.ask_token()
      })
    }
  }
}
