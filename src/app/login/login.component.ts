import { Component, OnInit } from '@angular/core';
import {SolWalletsService, Wallet} from "angular-sol-wallets";
import {HttpClient} from "@angular/common/http";
import {ActivatedRoute, Router} from "@angular/router";
import {UserService} from "../user.service";
import {GoogleLoginProvider, SocialAuthService} from "angularx-social-login";
import {Location} from "@angular/common";
import {ActiveDescendantKeyManager} from "@angular/cdk/a11y";
import {Network} from "ipfs-core/types/src/components/network";
import {NetworkService} from "../network.service";
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  message="";
  access_code="";

  constructor(
    private solWalletS : SolWalletsService,
    private httpClient : HttpClient,
    public router:Router,
    public user:UserService,
    public routes:ActivatedRoute,
    public network:NetworkService,
    public _location:Location,
    private socialAuthService: SocialAuthService
  ) { }

  ngOnInit(): void {
    this.message=this.routes.snapshot.queryParamMap.get("message") || "";
    if(environment.appli.indexOf("127.0.0.1")>-1){
      this.user.email="hhoareau@gmail.com";
      this._location.back();
    }
  }

  back(){
    this._location.back();
  }

  connect(network: string) {
    if(network=="elrond"){
      // @ts-ignore
      open(this.network.url_wallet(),"walletElrond")

    }

    if(network=="solana"){
      // @ts-ignore
      if(window.solflare || window.phantom){
        this.solWalletS.connect().then( (wallet:Wallet) => {
          this.user.init(wallet).then((profil:any)=>{
            this.back();
            // if(requis.length>0){
            //   if(profil.perms.indexOf("*")==-1 && profil.perms.indexOf(requis)==-1)
            //     this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
            // }
            //
          });
        }).catch(err => {
          console.log("Error connecting wallet", err );
          this.router.navigate(["faqs"],{queryParams:{"open":"not_authorized"}});
        })
      }
    }

    if(network=="google"){
      let servicePlatform = GoogleLoginProvider.PROVIDER_ID;
      this.socialAuthService.signIn(servicePlatform).then((socialUser) => {
        localStorage.setItem("email",socialUser.email);
        this.user.email=socialUser.email;
        this.user.name=socialUser.firstName + " "+ socialUser.lastName;
        this.back();
      })
    }

    if(network=="code"){
      if(this.access_code=="4271"){
        this.user.email="paul.dudule@gmail.com";
        this.user.name="paul";
        this.back();
      }
    }
  }
}
