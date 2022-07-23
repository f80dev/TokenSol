import { Component, OnInit } from '@angular/core';
import {SolWalletsService, Wallet} from "angular-sol-wallets";
import {HttpClient} from "@angular/common/http";
import {ActivatedRoute, Router} from "@angular/router";
import {UserService} from "../user.service";
import {GoogleLoginProvider, SocialAuthService} from "angularx-social-login";
import {Location} from "@angular/common";
import {ActiveDescendantKeyManager} from "@angular/cdk/a11y";

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {

  message="";

  constructor(
    private solWalletS : SolWalletsService,
    private httpClient : HttpClient,
    public router:Router,
    public user:UserService,
    public routes:ActivatedRoute,
    public _location:Location,
    private socialAuthService: SocialAuthService
  ) { }

  ngOnInit(): void {
    this.message=this.routes.snapshot.queryParamMap.get("message") || "";
  }

  back(){
    this._location.back();
  }

  connect(network: string) {
    if(network=="elrond"){
      // @ts-ignore
      open("wallet.elrond.com","walletElrond")

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
  }
}
