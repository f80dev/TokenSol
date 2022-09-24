import {WalletProvider} from "@elrondnetwork/erdjs-web-wallet-provider";
import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {$$, showMessage, url_wallet} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {WalletConnectProvider} from "@elrondnetwork/erdjs-wallet-connect-provider/out";
import {environment} from "../../environments/environment";
import {GoogleLoginProvider, SocialAuthService} from "angularx-social-login";
import {Location} from "@angular/common";
import {ActivatedRoute} from "@angular/router";
import {WALLET_PROVIDER_DEVNET, WALLET_PROVIDER_MAINNET} from "@elrondnetwork/erdjs-web-wallet-provider/out/constants";

@Component({
  selector: 'app-authent',
  templateUrl: './authent.component.html',
  styleUrls: ['./authent.component.css']
})
export class AuthentComponent implements OnInit {

  @Input() intro_message:string="Email / Adresse de blockchaine";
  @Input() network:string="elrond-devnet";
  @Input() explain_message:string="Adresse de votre wallet ou votre email si vous n'en avez pas encore";
  @Output('authent') onauthent: EventEmitter<any>=new EventEmitter();
  @Output('cancel') oncancel: EventEmitter<any>=new EventEmitter();
  @Output('logout') onlogout: EventEmitter<any>=new EventEmitter();
  @Input() showAccesCode=false;
  @Input() showGoogle=false;
  @Input() showNetwork=true;
  @Input() strong=true;

  qrcode: string="";
  access_code="";
  address: string="";


  constructor(
    public api:NetworkService,
    public user:UserService,
    public _location:Location,
    public routes:ActivatedRoute,
    private socialAuthService: SocialAuthService,
    public toast:MatSnackBar
  ) {
    this.user.provider=new WalletConnectProvider(
      "https://bridge.walletconnect.org",
      {
        onClientLogin: ()=> {
          if(this.user.provider){
            this.user.provider.getAddress().then((addr:string)=>{
              this.user.addr=addr;
              this.user.strong=true;
              if(this.user.provider)
                this.user.provider.getSignature().then((sign:string)=>{
                  $$("signature="+sign);
                })
              this.onauthent.emit(addr);
            })
          }
        },
        onClientLogout: ()=> {
          this.user.strong=false;
          this.onlogout.emit();
        }
      }
    );
  }

  ngOnInit(): void {
    if (this.user.provider){
      this.user.provider.init().then((b: boolean) => {
        if(this.user.provider){
          this.user.provider.login().then((s: string) => {
            this.qrcode = environment.server + "/api/qrcode/" + encodeURIComponent(s);
          });
        }
      });
    }

    if(environment.appli.indexOf("127.0.0.1")>-1){
      this.user.email="hhoareau@gmail.com";
      if(this.routes.snapshot.queryParamMap.get("goback")=='true')this._location.back();
    }
  }


  open_wallet() {
    if(this.network.indexOf("elrond")>-1) {
      let callback_url=environment.appli + this._location.path().split("?")[0];
      let url_wallet=this.network.indexOf("devnet")==-1 ? WALLET_PROVIDER_MAINNET : WALLET_PROVIDER_DEVNET;
      new WalletProvider(url_wallet).login({
        callbackUrl:callback_url
      }).then((result) => {
        this.user.addr = result;
        this.strong = true;
        this.onauthent.emit();
      })
    }
  }





  validate() {
    if(this.user && this.user.addr && this.user.addr.indexOf("@")==-1 && !this.api.isElrond(this.user.addr)){
      showMessage(this,"Le service n'est compatible qu'avec les adresses elrond");
    } else {
      this.onauthent.emit(this.user.addr);
    }
  }

  update_address() {
    //this.address=this.address.replace("@gmail","@gmail.com");
  }

  connect(network: string) {
    if(network=="elrond"){
      // @ts-ignore
      open(this.network.url_wallet(),"walletElrond")

    }

    if(network=="solana"){
      // @ts-ignore
      if(window.solflare || window.phantom){
        // this.solWalletS.connect().then( (wallet:Wallet) => {
        //   this.user.init(wallet).then((profil:any)=>{
        //     this.back();
        //     // if(requis.length>0){
        //     //   if(profil.perms.indexOf("*")==-1 && profil.perms.indexOf(requis)==-1)
        //     //     this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
        //     // }
        //     //
        //   });
        // }).catch((err:any) => {
        //   console.log("Error connecting wallet", err );
        //   this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
        // })
      }
    }

    if(network=="google"){
      let servicePlatform = GoogleLoginProvider.PROVIDER_ID;
      this.socialAuthService.signIn(servicePlatform).then((socialUser) => {
        this.user.email=socialUser.email;
        this.user.name=socialUser.firstName + " "+ socialUser.lastName;
        this.user.strong=true;
      })
    }

    if(network=="code"){
      if(this.access_code=="4271"){
        this.user.email="paul.dudule@gmail.com";
        this.user.name="paul";
        this.user.strong=true;
        this.back();
      }
    }
  }



  back(){
    this._location.back();
  }

}
