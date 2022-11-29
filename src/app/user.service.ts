import { Injectable } from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Router} from "@angular/router";
import {environment} from "../environments/environment";
import {$$, CryptoKey} from "../tools";
import {WalletConnectProvider} from "@elrondnetwork/erdjs-wallet-connect-provider/out";
import {NetworkService} from "./network.service";
import {Collection, Operation} from "../operation";
import {Subject} from "rxjs";



@Injectable({
  providedIn: 'root'
})
export class UserService {
  addr: string="";
  addr_change=new Subject<string>();
  key:CryptoKey | undefined;
  provider: WalletConnectProvider | undefined;
  collections:Collection[]=[];

  profil={
    routes:["/help","/about","/"],
    perms:["reload"],
    email:"",
    alias:"anonymous"
  };

  // private _wallet: Wallet | undefined;
  amount: number=0;
  strong:boolean=false;
  email: string="";
  name:string="";

  constructor(
    private httpClient : HttpClient,
    public router:Router,
    public network:NetworkService
  ) {

  }

  isConnected(strong:boolean=false) {
    return this.connected(strong);
  }

  login(message="") {
    if(!this.isConnected()){
      $$("Utilisateur non connecté --> redirection vers login");
      this.router.navigate(["login"],{queryParams:{message:message}});
    }
  }

  get_collection(){
    return new Promise((resolve, reject) => {
      this.network.get_collections(this.addr, this.network.network, false).subscribe((cols: any) => {
        this.collections = cols;
        resolve(cols);
      });
    });
  }


  init(addr:string,route=""){
    return new Promise((resolve, reject) => {
      if(addr.length>0){
        this.addr=addr
        if(addr.indexOf("@")>-1)this.email=addr;
          this.get_collection().then(()=>{
            this.httpClient.get(this.network.server_nfluent+"/api/perms/"+this.addr+"/?route="+route).subscribe((r:any)=>{
              this.profil = r;
              r.address=addr;
              this.addr_change.next(addr);
              resolve(r);
            },(err)=>{
              $$("!probleme de récupération des permissions")
              reject(err);
            });
          });
      }
    });
  }



  str_to_hex(text:string){
    let rc="";
    for(let i=0;i<text.length;i++){
      rc=rc+text.charCodeAt(i).toString(16);
    }
    return rc;
  }

  save_value(value:string){
    let data="SaveKeyValue@"+this.str_to_hex("")
  }


  connected(strong:boolean=false) {
    let rc=(this.addr && this.addr.length>0) || this.email.length>0;
    if(strong)rc=rc && this.strong;
    return rc;
  }


  logout() {
    this.addr="";
  }

  hasPerm(perm: string) {
    return this.profil.perms.indexOf(perm.toLowerCase())>-1;
  }


  //Getters and setters
  // get wallet(): Wallet {
  //   return <Wallet>this._wallet;
  // }
  //
  // set wallet(value: Wallet) {
  //   this._wallet = value;
  // }


  open_elrond_authent() {
    //voir : https://docs.elrond.com/wallet/webhooks/#:~:text=The%20web%20wallet%20webhooks%20allow,form%20with%20the%20provided%20arguments.

  }

  connect(requis:string="",network="elrond-devnet"){
    return new Promise((resolve, reject) => {
      resolve({});
    });
  }


  disconnect(){
    // this.solWalletS.disconnect().then(()=>{
    //   this.logout();
    // });
  }

  signMessage(){
    // this.solWalletS.signMessage("HELLO WORLD!").then( (signature:any) => {
    //   console.log('Message signed:', signature);
    // }).catch( (err:any) => {
    //   console.log('err transaction', err );
    // })
  }


  makeATransfer( myCompanyPublicKey : string, solAmmount : number){
    // this.solWalletS.signAndSendTransfer(myCompanyPublicKey, solAmmount ).then( (signature:any) => {
    //   console.log('Transfer successfully opered:', signature);
    // }).catch( (err:any) => {
    //   console.log('Error transaction', err );
    // });
  }


  sendTransferToServer( myCompanyPublicKey : string, solAmmount : number) {
    // this.solWalletS.signTransfer(myCompanyPublicKey, solAmmount).then((buffer:any) => {
    //   this.httpClient.post('https://myserver.io/myAPI/makeTransfer', {transferRow: buffer}).subscribe((res:any) => {
    //     console.log('Transfer successfully opered:', res.signature);
    //   });
    // }).catch((err:any) => {
    //   console.log('Error transaction', err);
    // });
  }

  find_collection(sel_collection: string) {
    if(!sel_collection)return null;
    for(let col of this.collections)
      if(col.id==sel_collection)return col;
    return null;
  }
}
