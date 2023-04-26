import { Component, OnInit } from '@angular/core';
import {Location} from "@angular/common";
import {UserProfil, UserService} from "../user.service";
import {decrypt, encrypt, getParams, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {MatSnackBar} from "@angular/material/snack-bar";


@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  title="";
  show_registration: boolean=false;
  access_code: string="";
  email: any="";
  show_wallet_authent: boolean=false;


  constructor(
    public _location:Location,
    public user:UserService,
    public network:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
  ) { }

  ngOnInit(): void {
    this.network.check_network(this.router);

    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("message") || params.hasOwnProperty("title"))this.title=params["title"] || params["message"];
      this.access_code=decrypt(localStorage.getItem("access_code"));
      this.email=decrypt(localStorage.getItem("email"));
      this.authent();
    })
  }

  authent() {
    if(this.access_code && this.email){
      this.user.setProfil(this.email,this.access_code).then(()=>{
        localStorage.setItem("access_code",encrypt(this.access_code));
        localStorage.setItem("email",encrypt(this.email));
        this.user.profil.email=this.email;
        this.user.strong=true;
        this.user.verified_address=true;
        this._location.back()
      },(err:any)=>{
        showMessage(this,err.error);
        this.show_registration=false;
        localStorage.removeItem("access_code");
        localStorage.removeItem("email");
        this.access_code="";
      });
    }
  }


  registration($event: { strong: boolean; nftchecked: boolean; address: string }) {
    this.network.registration($event.address).subscribe((p:UserProfil)=>{
      if(p.message=="already exists"){
        showMessage(this,"Ce compte est déjà inscrit, votre code d'accès a été renvoyé sur votre mail");
      } else {
        showMessage(this,"Consultez votre boite mail pour récupérer votre code d'accès");
      }
      this.show_registration=false;

    })
  }

  resend_code() {
    if(this.email.length==0){
      showMessage(this,"Renseigner votre mail afin de recevoir votre code d'accès sur votre boite mail")
      return;
    }
    this.network.registration(this.email).subscribe(()=>{
      showMessage(this,"Consulter votre boite mail pour retrouver votre code d'accès à TokenForge")
    })
  }

  login_with_wallet($event: { strong: boolean; nftchecked: boolean; address: string; provider: any }) {
    this.user.init_wallet_provider($event.provider,$event.address)
    this.show_wallet_authent=false;
    this._location.back()
  }
}
