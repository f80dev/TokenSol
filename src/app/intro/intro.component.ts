import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {UserService} from "../user.service";
import {Router} from "@angular/router";
import {setParams} from "../../tools";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-intro',
  templateUrl: './intro.component.html',
  styleUrls: ['./intro.component.css']
})
export class IntroComponent implements OnInit {

  version: any;

  constructor(public user:UserService,public router:Router,public network:NetworkService) {
    this.version=environment.version;
  }

  ngOnInit(): void {
  }

  open_create() {
    this.router.navigate(["creator"])
        // ,{queryParams:{params:setParams({
        //   "toolbar":false,
        //   "networks":this.network.config["NETWORKS"]
        // })}})
  }
}
