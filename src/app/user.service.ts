import {Injectable, OnDestroy} from '@angular/core';
import {HttpClient} from "@angular/common/http";
import {Router} from "@angular/router";
import {$$, CryptoKey, detect_network, isLocal} from "../tools";
import {NetworkService} from "./network.service";
import {Collection} from "../operation";
import {Subject} from "rxjs";
import {environment} from "../environments/environment";
import {Merchant} from "./payment/payment.component";

export interface UserProfil {
  routes:string[]
  perms:string[]
  email:string
  alias:string
  access_code:string
  message:string
}

//Le user est connecté si son address blockchain est vérifiée ou si son email est vérifié

@Injectable({
  providedIn: 'root'
})
export class UserService implements OnDestroy {
  addr: string = "";              //Adresse sur la blockchain

  addr_change = new Subject<string>();
  profil_change = new Subject<UserProfil>();
  params_available=new Subject<any>()

  buy_method: "crypto" | "fiat" | "" = "";

  key: CryptoKey | undefined;
  provider: any | undefined;
  collections: Collection[] = [];

  merchant: Merchant=environment.merchant;

  profil: UserProfil = {
    routes: ["/help", "/about", "/"],
    perms: ["reload"],
    email: "",
    alias: "anonymous",
    access_code: "",
    message:""
  };

  // private _wallet: Wallet | undefined;
  amount: number = 0;
  strong: boolean = false;
  name: string = "";
  balance: number = 0;
  nfts_to_mint: any[] = []
  advance_mode: boolean = false;
  toolbar_visible: boolean = true;

  params:any={appname:""}                             //Enregistrement des parametres au lancement de l'appli
  verified_address: Boolean=false;
  wallet_provider: any;                   //Instance d'acces au wallet distant
  theme_mode: boolean=false;

  constructor(
      private httpClient: HttpClient,
      public router: Router,
      public network: NetworkService
  ) {

  }

  isConnected(_with : "wallet" | "email" | "" ="") : boolean {
    if(_with!="wallet" && this.profil && this.profil.email.length>0 && this.verified_address)return true;
    if(_with!="email" && this.wallet_provider!=undefined && this.addr.length>0)return true;
    return false;
  }


  login(message = "") {
    if (!this.isConnected()) {
      $$("Utilisateur non connecté --> redirection vers login");
      this.router.navigate(["login"], {queryParams: {message: message}});
    }
  }

  get_collection(addr: string, network: string) {
    //Retourne l'ensemble des collections disponibles
    return new Promise<Collection[]>((resolve, reject) => {
      this.network.get_collections(addr, network, false).subscribe((cols: Collection[]) => {
        this.collections = cols;
        resolve(cols);
      }, (err: any) => {
        reject(err);
      });
    });
  }

  setProfil(email: string, access_code: string) {
    return new Promise((resolve, reject) => {
      if (!access_code) {
        reject();
      } else {
        this.httpClient.get<UserProfil>(this.network.server_nfluent + "/api/login/" + email + "/" + access_code + "/").subscribe((p: UserProfil) => {
          this.profil = p;
          this.profil_change.next(p);
          resolve(p);
        }, (err) => {
          $$("!probleme de récupération des permissions");
          reject(err);
        });
      }
    });
  }

  async init_wallet_provider(wallet_provider:any,addr:string=""){
    if(wallet_provider!=undefined){
      this.wallet_provider=wallet_provider;
      let r=await this.init(
          addr.length>0 ? addr : wallet_provider.account.address,
          "",
          false,
          true
      )
      this.addr_change.next(this.addr);
    }
  }

  init(addr: string, network: string="", with_collections = true,verified_address=false,email="") {
    return new Promise((resolve, reject) => {
      if(!addr)reject();
      else{
        if(network.length==0)network=detect_network(addr!);
        if(email.length>0)this.profil.email=email;
        this.verified_address=verified_address;
        this.network.get_account(addr!, network).subscribe((result: any) => {
          let r=result[0];
          this.balance = r.amount || 0;
          this.key=this.network.find_key_by_address(r.address);
          if(!this.key){
            this.key = {
              balance: r.balance,
              encrypt: "",
              explorer: "",
              name: r.name,
              secret_key: r.secret_key,
              address: r.address,
              qrcode: "",
              unity: r.unity
            }
          }
          this.addr = r.address;
          if (with_collections) {
            this.get_collection(this.addr, network).then((cols:Collection[]) => {
              this.collections=cols;
              this.addr_change.next(r.address);
              resolve(r.address);
            });
          } else {
            this.collections = [];
          }
        })
      }
    })
  }


  str_to_hex(text: string) {
    let rc = "";
    for (let i = 0; i < text.length; i++) {
      rc = rc + text.charCodeAt(i).toString(16);
    }
    return rc;
  }

  save_value(value: string) {
    let data = "SaveKeyValue@" + this.str_to_hex("")
  }


  logout() {
    $$("Déconnexion / Logout");
    try {
      if(this.wallet_provider)this.wallet_provider.logout()
    }  catch (e) {}
    this.addr = "";
    this.profil = {
      alias: "", email: "", perms: [], routes: [], access_code: "",message:""
    }
    localStorage.removeItem("access_code");
  }

  hasPerm(perm: string) {
    if (this.profil.perms.indexOf("admin") > -1) return true; //L'admin a toutes les permissions
    let rc = this.profil.perms.indexOf(perm.toLowerCase()) > -1;
    return rc
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

  connect(requis: string = "", network = "elrond-devnet") {
    return new Promise((resolve, reject) => {
      resolve({});
    });
  }


  signMessage() {
    // this.solWalletS.signMessage("HELLO WORLD!").then( (signature:any) => {
    //   console.log('Message signed:', signature);
    // }).catch( (err:any) => {
    //   console.log('err transaction', err );
    // })
  }


  makeATransfer(myCompanyPublicKey: string, solAmmount: number) {
    // this.solWalletS.signAndSendTransfer(myCompanyPublicKey, solAmmount ).then( (signature:any) => {
    //   console.log('Transfer successfully opered:', signature);
    // }).catch( (err:any) => {
    //   console.log('Error transaction', err );
    // });
  }


  sendTransferToServer(myCompanyPublicKey: string, solAmmount: number) {
    // this.solWalletS.signTransfer(myCompanyPublicKey, solAmmount).then((buffer:any) => {
    //   this.httpClient.post('https://myserver.io/myAPI/makeTransfer', {transferRow: buffer}).subscribe((res:any) => {
    //     console.log('Transfer successfully opered:', res.signature);
    //   });
    // }).catch((err:any) => {
    //   console.log('Error transaction', err);
    // });
  }

  find_collection(sel_collection: string | undefined) {
    if (!sel_collection) return null;
    for (let col of this.collections)
      if (col.id == sel_collection) return col;
    return null;
  }

  refresh_balance() {
    return this.network.getBalance(this.addr,this.network.network).subscribe((balance: any) => {
      this.balance = balance
    });
  }

  delete_account() {
    return new Promise((resolve, reject) => {
      this.network.delete_account(this.profil.access_code).subscribe(() => {
        this.logout();
        resolve(true);
      })
    });

  }

  change_access_code(new_password: string) {
    this.network.update_access_code(this.profil.access_code, new_password).subscribe(() => {
    })
  }

  ngOnDestroy(): void {
    this.logout();
  }

}
