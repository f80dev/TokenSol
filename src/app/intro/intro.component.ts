import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {UserService} from "../user.service";
import {Router} from "@angular/router";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-intro',
  templateUrl: './intro.component.html',
  styleUrls: ['./intro.component.css']
})
export class IntroComponent implements OnInit {

  version: any;
  logo=environment.logo;

  constructor(public user:UserService,public router:Router,public network:NetworkService) {
    this.version=environment.version;
  }

  ngOnInit(): void {
    this.logo=this.user.params.logo;
  }

  open_create() {
    this.router.navigate(["creator"])
        // ,{queryParams:{params:setParams({
        //   "toolbar":false,
        //   "networks":this.network.config["NETWORKS"]
        // })}})
  }
}
