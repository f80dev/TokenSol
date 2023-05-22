import {Component, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";
import {ActivatedRoute} from "@angular/router";
import {
  getParams,
  CryptoKey,
  newCryptoKey,
  showMessage,
  showError,
  $$,
  isEmail,
  Bank,
  extract_bank_from_param
} from "../../tools";
import {environment} from "../../environments/environment";
import {wait_message} from "../hourglass/hourglass.component";
import {MatSnackBar} from "@angular/material/snack-bar";
import {DeviceService} from "../device.service";

@Component({
  selector: 'app-bank',
  templateUrl: './bank.component.html',
  styleUrls: ['./bank.component.css']
})
export class BankComponent implements OnInit {
  addr: string="";
  show_can_close: boolean=false;
  bank:Bank | undefined
  balance: number=0;
  message="";
  transaction: any;
  token: any;
  border="2%";
  size="90%";
  background_image: string="";

  public constructor(
    public network:NetworkService,
    public _location:Location,
    public device:DeviceService,
    public toast:MatSnackBar,
    public routes:ActivatedRoute,
  ){}


  refund() {
    if(this.bank && this.addr.length>0){
      let bank:CryptoKey=newCryptoKey("","theBank",this.bank!.miner);
      wait_message(this,"Ajout de "+this.bank!.refund+" "+this.token.name+" à votre compte ...");

      this.network.refund(bank,this.addr,this.bank?.token,this.bank!.refund,"Rechargement",this.bank.network).subscribe((result)=>{
        $$("Fin du rechargement ",result);
        this.transaction=result;
        wait_message(this)
        if(result.error==""){
          showMessage(this,"Vous avez récupérer de nouveaux "+this.token.name);
          this.refresh_balance().then(()=>{
            this.show_can_close=true;
          })
        } else {
          showMessage(this,result.error);
        }

      },(err:any)=>{showError(this,err)})
    }
  }


  async ngOnInit() {
    this.device.isHandset$.subscribe((isHandset)=>{
      if(isHandset){this.border="0px";this.size="100%";}
    })

    let params:any=await getParams(this.routes);
    if(params.merchant){
      this.bank=params.bank || environment.bank || {}
    } else {
      this.bank=extract_bank_from_param(params) || environment.bank;
    }
    if(this.bank){
      if(params.claim)this.bank!.title=params.claim;
      this.network.get_token(this.bank.token,this.bank.network).subscribe((r)=>{
        this.token=r;
      })
      this.network.init_network(this.bank.network);
    }
    this.background_image=params.visual || "";
    this.addr=params.addr || params.address || localStorage.getItem("faucet_addr") || "";
    this.refresh_balance();
  }


  save_local(){
    localStorage.setItem("faucet_addr",this.addr);
  }


  refresh_balance(){
    return new Promise((resolve,reject) => {
      if(this.addr && this.addr.length>0){
        this.network.getBalance(this.addr,this.network.network,this.bank!.token).subscribe((result:any)=>{
          this.balance=Math.round(result[0].balance/1e16)/100;
          resolve(true);
        },(err)=>{reject(err);})
      }
    })
  }

  update_address($event: { strong: boolean; address: string; provider: any }) {
    this.addr=$event.address;
    if(!isEmail(this.addr)){
      this.refresh_balance();
    } else {
      this.balance=0;
    }

    this.save_local();
  }


  change_addr() {
    this._location.replaceState("bank","")
    this.addr="";
    this.balance=0;
    this.save_local();
  }

  cancel() {
    this.change_addr();
  }
}
