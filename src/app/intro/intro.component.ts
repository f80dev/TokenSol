import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {UserService} from "../user.service";

@Component({
  selector: 'app-intro',
  templateUrl: './intro.component.html',
  styleUrls: ['./intro.component.css']
})
export class IntroComponent implements OnInit {
  appname: any;
  version: any;

  constructor(public user:UserService) {
    this.appname=this.user.appname;
    this.version=environment.version;
  }

  ngOnInit(): void {
  }

}
