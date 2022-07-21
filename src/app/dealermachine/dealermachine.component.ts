import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {$$, decrypt, getParams, hasWebcam, showMessage} from "../../tools";
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
  ope: any=null;
  webcam: boolean=true;
  mining: any={};

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

    let ope=getParams(this.routes,"ope");
    this.nft=getParams(this.routes,"token",{});
    this.price=getParams(this.routes,"price",this.nft.marketplace.initial_price);
    this.mining=getParams(this.routes,"mining");

    this.selfWalletConnexion=getParams(this.routes,"selfWalletConnexion",false);

    if(ope){
      this.network.get_operations(ope).subscribe((ope:any)=>{
        this.ope=ope;
        this.mining=getParams(this.routes,"mining",this.ope.lazy_mining);

        if(this.nft=={}){
          let id=getParams(this.routes,"id","");
          this.network.get_nft_from_db(id).subscribe((nft:any)=>{
            this.nft=nft || {};
            if(!nft){
              this.lost()
            }
          });
        }
      })
    }

  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";
  price: string="";
  hasWebcam=true;
  billing_address="";
  selfWalletConnexion: boolean=false;

  lost(){
    $$("Lost")
    if(this.ope && this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.looser.message,this.ope.lottery.end_process.looser.redirection)
    } else {
      this.end_process("Ce NFT vous a échapé");
    }
  }

  win(){
    $$("Win")
    if(this.ope && this.ope.lottery.hasOwnProperty("end_process")){
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

    let addr=this.alias.transform(this.address,"pubkey");
    if(this.nft.hasOwnProperty("id")){
      $$("Ce token est issue d'une base de données, donc non miné");
        let id=this.nft["id"];
        if(this.ope)this.message=this.ope.store.support.buy_message;
        this.network.mint_for_contest(addr,id,this.ope,this.mining.miner,this.mining.metadata_storage,this.mining.network,this.nft).subscribe((r:any)=>{
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

        if(this.nft.hasOwnProperty("account")){
          $$("Ce token est déjà miné, on se contente de le transférer");
          let mint_addr=this.nft["account"]["data"]["parsed"]["info"]["mint"]
          let owner=this.nft["account"]["data"]["parsed"]["info"]["owner"]
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
