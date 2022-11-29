import { Component, OnInit } from '@angular/core';
import {Location} from "@angular/common";
import {UserService} from "../user.service";
import {ADDR_ADMIN, EMAIL_ADMIN} from "../../definitions";
import {getParams} from "../../tools";
import {ActivatedRoute} from "@angular/router";


@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {
  title="";


  constructor(
    public _location:Location,
    public user:UserService,
    public routes:ActivatedRoute
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("message") || params.hasOwnProperty("title"))this.title=params["title"] || params["message"];
    })
  }

  authent($event: { strong: boolean; nftchecked: boolean; address: string }) {
    if($event.strong){
      let addr=$event.address;
      if(!addr || addr=="")addr=ADDR_ADMIN;
      this.user.init(addr).then(()=>{
        this._location.back();
      });
    }
  }
}
