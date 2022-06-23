import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="paul.dudule@gmail.com";
  wallet_link: string="";
  nft:any={};
  final_message="";
  ope: any={};

  constructor(
    public routes:ActivatedRoute,
    public _location:Location,
    public network:NetworkService,
    public toast:MatSnackBar,
    public router:Router,
    public alias:AliasPipe
  ) { }

  ngOnInit(): void {
    this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((ope:any)=>{
      this.ope=ope;
      this.network.get_nft_from_db(this.routes.snapshot.queryParamMap.get("id") || "").subscribe((nft:any)=>{
        this.nft=nft || {};
        if(!nft){
          this.lost()
        } else {
          this.price=""+nft.marketplace.initial_price;
        }
      });
    })
  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";
  price: string="";

  lost(){
    if(this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.looser.message,this.ope.lottery.end_process.looser.redirection)
    } else {
      this.end_process("Ce NFT vous a échapé");
    }
  }

  win(){
    if(this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.winner.message,this.ope.lottery.end_process.winner.redirection)
    } else {
      this.end_process("Ce NFT est le votre.");
    }
  }

  end_process(sMessage:string,rediction=null){
    if(rediction){
      showMessage(this,sMessage);
      setTimeout(()=>{
        open(this.ope.lottery.end_process.winner.redirection);
        },500);
    } else {
      this.message=sMessage+". Vous pouvez fermer cette écran";
    }
  }

  valide() {
    let id=this.routes.snapshot.queryParamMap.get("id")  || "";
    let addr=this.alias.transform(this.address,"pubkey");
    if(id){
        this.message="Demande en cours";
        this.network.mint_for_contest(addr,id,this.ope,this.ope.lottery.miner,this.ope.metadata_storage).subscribe((r:any)=>{
          this.nft=null;
          this.message="";
          if(r.error.length>0){
            this.message=r.error+". ";
            this.lost();
          } else {
            this.win();
          }
        },(err)=>{
          this.message="";
          this.lost();
        })
    }

  }


  onLoadPaymentData($event: any) {
    if($event.returnValue)
      this.valide();
  }
}
