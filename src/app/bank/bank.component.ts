import {Component, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";
import {ActivatedRoute} from "@angular/router";
import {
  getParams,
  showMessage,
  showError,
  $$,
  isEmail,
  Bank,
  extract_bank_from_param, apply_params
} from "../../tools";
import {environment} from "../../environments/environment";
import {wait_message} from "../hourglass/hourglass.component";
import {MatSnackBar} from "@angular/material/snack-bar";
import {DeviceService} from "../device.service";
import {StyleManagerService} from "../style-manager.service";
import {UserService} from "../user.service";

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
  visual: string="";
  background: string="";
  end_message: string = "";

  public constructor(
    public network:NetworkService,
    public _location:Location,
    public device:DeviceService,
    public toast:MatSnackBar,
    public user:UserService,
    public style:StyleManagerService,
    public routes:ActivatedRoute,
  ){
    this.user.params_available.subscribe((params:any)=>{
      this.refresh(params);
    })
  }


  refresh(params:any){
    if(params.merchant){
      this.bank=params.bank || environment.bank || {}
    } else {
      this.bank=extract_bank_from_param(params) || environment.bank;
    }
    if(this.bank){
      if(params.claim)this.bank!.title=params.claim;
      this.network.get_token(this.bank.token,this.bank.network).subscribe((r)=>{
        this.token=r;
        apply_params(this,params,environment.bank)
        if(!params.style)this.style.setStyle("theme","nfluent-dark-theme.css")
        this.addr=params.addr || params.address || localStorage.getItem("faucet_addr") || "";
        this.refresh_balance();
        this.network.init_network(this.bank!.network);
      })

    }

  }

  refund() {
    if(this.bank && this.addr.length>0){
      wait_message(this,"Ajout de "+this.bank!.refund+" "+this.token.name+" à votre compte ...");

      this.network.refund(this.bank,this.addr).subscribe((result)=>{
        $$("Fin du rechargement ",result);
        this.addr=result.address;
        this.transaction=result;
        wait_message(this)
        if(result.error==""){
          this.end_message="Vous avez récupérer de nouveaux "+this.token.name
          this.refresh_balance().then(()=>{this.show_can_close=true;})
        } else {
          this.end_message=result.error;
          wait_message(this)
          this.show_can_close=true
        }

      },(err:any)=>{
        showError(this,err)
      })
    }
  }


  async ngOnInit() {
    this.device.isHandset$.subscribe((isHandset)=>{
      if(isHandset){this.border="0px";this.size="100%";}
    })

    // let params:any=await getParams(this.routes);
    // this.refresh(params);
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
    this.addr="";
    this.balance=0;
    this.save_local();
  }

  cancel() {
    this.change_addr();
  }

  buy() {

  }
}
