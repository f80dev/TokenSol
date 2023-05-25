import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {ActivatedRoute} from "@angular/router";
import {apply_params, getParams} from "../../tools";
import {Location} from "@angular/common";

@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css']
})
export class AboutComponent implements OnInit {

  appname="";
  website=environment.website;
  version=environment.version;

  constructor(
      public routes:ActivatedRoute,
      public _location:Location
  ) { }

  async ngOnInit() {
    let params=await getParams(this.routes)
    apply_params(this,params,environment);

  }

}
