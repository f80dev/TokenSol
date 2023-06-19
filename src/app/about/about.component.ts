import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {ActivatedRoute, Router} from "@angular/router";
import {apply_params, getParams} from "../../tools";
import {Location} from "@angular/common";
import {StyleManagerService} from "../style-manager.service";
import {UserService} from "../user.service";
import {NgNavigatorShareService} from "ng-navigator-share";

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

  constructor(
      public routes:ActivatedRoute,
      public _location:Location,
      public style:StyleManagerService,
      public user:UserService,
      public router:Router,
      public ngShare:NgNavigatorShareService
  ) { }

  async ngOnInit() {
    let params=await getParams(this.routes)
    apply_params(this,params,environment);

  }

  open_share() {
    this.ngShare.share({
      title:this.user.params.appname,
      text:this.user.params.claim,
      url:this.router.url
    })
  }

}
