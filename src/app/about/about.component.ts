import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {ActivatedRoute} from "@angular/router";
import {apply_params, getParams} from "../../tools";
import {Location} from "@angular/common";
import {StyleManagerService} from "../style-manager.service";
import {UserService} from "../user.service";

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
  logo="./assets/icons/icon_nfluent_256.png"

  constructor(
      public routes:ActivatedRoute,
      public _location:Location,
      public style:StyleManagerService,
      public user:UserService
  ) { }

  async ngOnInit() {
    if(this.user.params && this.user.params.appname && this.user.params.appname.length>0){
      apply_params(this,this.user.params,environment);
    }else{
      let params=await getParams(this.routes)
      apply_params(this,params,environment);

    }
  }

}
