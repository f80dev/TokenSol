import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {$$, decrypt, hasWebcam, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {UserService} from "../user.service";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";
  wallet_link: string="";
  nft:any={};
  final_message="";
  ope: any={};
  webcam: boolean=true;

  constructor(
    public routes:ActivatedRoute,
    public _location:Location,
    public userService:UserService,
    public network:NetworkService,
    public toast:MatSnackBar,
    public router:Router,
    public alias:AliasPipe
  ) { }


  ngOnInit(): void {
    hasWebcam(this.webcam);
    let id=this.routes.snapshot.queryParamMap.get("id") || "";
    let ope=this.routes.snapshot.queryParamMap.get("ope") || "";
    let param=this.routes.snapshot.queryParamMap.get("param") || "";
    let token=this.routes.snapshot.queryParamMap.get("token") || "";
    let pay=true;
    if(param!=""){
      let _param=decrypt(param).split("&&&");
      ope=_param[0];
      token=JSON.parse(atob(_param[1]))
      pay=_param[2]=="true";
    }


    this.network.get_operations(ope).subscribe((ope:any)=>{
      this.ope=ope;
      if(token.length>0){
        this.nft=JSON.parse(atob(token));
        this.price=""+this.nft.marketplace.initial_price;
      }else{
        this.network.get_nft_from_db(id).subscribe((nft:any)=>{
          this.nft=nft || {};
          if(!nft){
            this.lost()
          } else {
            this.price=""+nft.marketplace.initial_price;
          }
        });
      }

    })
  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";
  price: string="";
  hasWebcam=true;
  billing_address="";

  lost(){
    $$("Lost")
    if(this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.looser.message,this.ope.lottery.end_process.looser.redirection)
    } else {
      this.end_process("Ce NFT vous a échapé");
    }
  }

  win(){
    $$("Win")
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
        },3500);
    } else {
      this.message=sMessage+". Vous pouvez fermer cette écran";
    }
  }


  valide() {
    let _token:any={}
    let token=this.routes.snapshot.queryParamMap.get("token") || "";
    if(token.length>0)_token=JSON.parse(atob(token));

    let addr=this.alias.transform(this.address,"pubkey");
    if(_token.hasOwnProperty("id")){
        let id=_token["id"];
        this.message=this.ope.store.support.buy_message;
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
    }else{
        if(_token.hasOwnProperty("account")){
          let mint_addr=_token["account"]["data"]["parsed"]["info"]["mint"]
          let owner=_token["account"]["data"]["parsed"]["info"]["owner"]
          if(mint_addr.length>0){
            this.network.transfer_to(mint_addr,addr,owner).subscribe(()=>{
              showMessage(this,"Transféré");
            })
          }
        }
      }
  }


  onLoadPaymentData($event: any) {
    if($event.returnValue)
      this.valide();
  }

  open_wallet(network: string) {
    this.userService.connect("",network).then((r:any)=>{
      this.address=r.address;
    })
  }

  onflash($event: any) {
    this.address=$event.data;
  }
}
