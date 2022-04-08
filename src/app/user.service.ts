import { Injectable } from '@angular/core';
import {PERMS} from "../definitions";
import {SolWalletsService, Wallet} from "angular-sol-wallets";
import {HttpClient} from "@angular/common/http";

@Injectable({
  providedIn: 'root'
})
export class UserService {
  addr: string | undefined;
  perms: string[]=[];
  private _wallet: Wallet | undefined;
  amount: number=0;

  constructor(
    private solWalletS : SolWalletsService,
    private httpClient : HttpClient
  ) {
  }


  init(wallet:Wallet){
    this._wallet=wallet;
    this.addr=wallet.publicKey?.toBase58();
    if(Object.keys(PERMS).indexOf(<string>this.addr)>-1) {
      this.perms = PERMS[<string>this.addr];
    } else {
      this.perms=PERMS['connected'];
    }
  }



  connected() {
    return this.addr && this.addr.length>0;
    this.perms=PERMS['connected'];
  }

  logout() {
    this.addr="";
    this.perms=PERMS['anonymous'];
  }

  hasPerm(perm: string) {
    return this.perms.indexOf(perm.toLowerCase())>-1;
  }


  //Getters and setters
  get wallet(): Wallet {
    return <Wallet>this._wallet;
  }

  set wallet(value: Wallet) {
    this._wallet = value;
  }


  connect(func:Function | null){
    this.solWalletS.connect().then( (wallet:Wallet) => {
      this.init(wallet);
      console.log("Wallet connected successfully with this address:", wallet.publicKey);
      if(func)func();
    }).catch(err => {
      console.log("Error connecting wallet", err );
    })
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
