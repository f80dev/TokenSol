import { Injectable } from '@angular/core';
import {SolWalletsService, Wallet} from "angular-sol-wallets";
import {HttpClient} from "@angular/common/http";
import {Router} from "@angular/router";
import {environment} from "../environments/environment";
import {$$} from "../tools";



@Injectable({
  providedIn: 'root'
})
export class UserService {
  addr: string | undefined;
  profil={
    routes:["/help","/about","/"],
    perms:["reload"],
    email:"",
    alias:"anonymous"
  };

  private _wallet: Wallet | undefined;
  amount: number=0;

  constructor(
    private solWalletS : SolWalletsService,
    private httpClient : HttpClient,
    public router:Router
  ) {
  }


  init(wallet:Wallet,route=""){
    return new Promise((resolve, reject) => {
      this._wallet=wallet;
      this.addr=wallet.publicKey?.toBase58();
      this.httpClient.get(environment.server+"/api/perms/"+this.addr+"/?route="+route).subscribe((r:any)=>{
        this.profil = r;
        r.address=wallet.publicKey?.toBase58();
        resolve(r);
      },(err)=>{
        $$("!probleme de récupération des permissions")
        reject(err);
      })
    });

  }



  connected() {
    return this.addr && this.addr.length>0;
  }


  logout() {
    this.addr="";
  }

  hasPerm(perm: string) {
    return this.profil.perms.indexOf(perm.toLowerCase())>-1;
  }


  //Getters and setters
  get wallet(): Wallet {
    return <Wallet>this._wallet;
  }

  set wallet(value: Wallet) {
    this._wallet = value;
  }


  connect(requis:string="",network="solana"){
    return new Promise((resolve, reject) => {
      if(network=="elrond"){
        // @ts-ignore
        open("wallet.elrond.com","walletElrond")
      }else{
        // @ts-ignore
        if(window.solflare || window.phantom){
          this.solWalletS.connect().then( (wallet:Wallet) => {
            this.init(wallet).then((profil:any)=>{
              if(requis.length>0){
                if(profil.perms.indexOf("*")==-1 && profil.perms.indexOf(requis)==-1)
                  this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
              }
              resolve(profil);
            }).catch(()=>{reject();});
          }).catch(err => {
            console.log("Error connecting wallet", err );
            this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
            reject(err);
          })
        }
      }
    });
  }


  disconnect(){
    this.solWalletS.disconnect().then(()=>{
      this.logout();
    });
  }

  signMessage(){
    this.solWalletS.signMessage("HELLO WORLD!").then( signature => {
      console.log('Message signed:', signature);
    }).catch( err => {
      console.log('err transaction', err );
    })
  }


  makeATransfer( myCompanyPublicKey : string, solAmmount : number){
    this.solWalletS.signAndSendTransfer(myCompanyPublicKey, solAmmount ).then( signature => {
      console.log('Transfer successfully opered:', signature);
    }).catch( err => {
      console.log('Error transaction', err );
    });
  }


  sendTransferToServer( myCompanyPublicKey : string, solAmmount : number) {
    this.solWalletS.signTransfer(myCompanyPublicKey, solAmmount).then(buffer => {
      this.httpClient.post('https://myserver.io/myAPI/makeTransfer', {transferRow: buffer}).subscribe((res:any) => {
        console.log('Transfer successfully opered:', res.signature);
      });
    }).catch(err => {
      console.log('Error transaction', err);
    });
  }

}
