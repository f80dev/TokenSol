import { Component, OnInit } from '@angular/core';
import {Location} from "@angular/common";
import {UserProfil, UserService} from "../user.service";
import {ADDR_ADMIN} from "../../definitions";
import {decrypt, encrypt, getParams, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {_prompt} from "../prompt/prompt.component";
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


  constructor(
    public _location:Location,
    public user:UserService,
    public network:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("message") || params.hasOwnProperty("title"))this.title=params["title"] || params["message"];
      if(localStorage.getItem("access_code")){
        this.authent(decrypt(localStorage.getItem("access_code")));
      }
    })
  }

  authent(access_code:string | null) {
    if(access_code){
      this.user.setProfil(access_code).then(()=>{
        localStorage.setItem("access_code",encrypt(access_code));
        //if(this.title.length>0){
          this._location.back()
        // }else{
        //   this.router.navigate(["settings"]);
        // }
      },(err:any)=>{
        showMessage(this,err.error);
        this.show_registration=false;
        this.access_code="";
      });
    }
  }


  registration($event: { strong: boolean; nftchecked: boolean; address: string }) {
    this.network.registration($event.address).subscribe((p:UserProfil)=>{
      this.show_registration=false;
      showMessage(this,"Consultez votre boite mail pour récupérer votre code d'accès");
    })
  }
}
