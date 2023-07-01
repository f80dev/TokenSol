import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {ActivatedRoute, Router} from "@angular/router";
import {apply_params, getParams} from "../../tools";
import {Location} from "@angular/common";
import {StyleManagerService} from "../style-manager.service";
import {UserService} from "../user.service";
import {NgNavigatorShareService} from "ng-navigator-share";
import {_prompt} from "../prompt/prompt.component";

@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css']
})
export class AboutComponent implements OnInit {

  website=environment.website;
  company="NFluent"
  version=environment.version;
  cgu=environment.website+"/cgu.html"
  contact=""
  logo="./assets/logo.png"
  exist_faqs: boolean = false;
  show_admin: boolean = false;

  constructor(
      public routes:ActivatedRoute,
      public _location:Location,
      public style:StyleManagerService,
      public user:UserService,
      public router:Router,
      public ngShare:NgNavigatorShareService
  ) { }

  async ngOnInit() {
    let params:any=await getParams(this.routes)
    apply_params(this,params,environment);
    this.exist_faqs=(params.faqs || environment.faqs || "").length>0
    let env:any=environment
    this.show_admin=env.hasOwnProperty("admin_password")
  }

  open_share() {
    this.ngShare.share({
      title:this.user.params.appname,
      text:this.user.params.claim,
      url:this.router.url
    })
  }

  open_faqs() {
    this.router.navigate(["faqs"])
  }

  async open_admin() {
    // @ts-ignore
    if(!environment.admin_password || environment.admin_password==""){
      this.router.navigate(["admin"])
    }else{
      let conf=await _prompt(this,"Password administrateur","","","text","ok","annuler",false)
      // @ts-ignore
      if(conf==environment.admin_password)this.router.navigate(["admin"]);
    }

  }
}
