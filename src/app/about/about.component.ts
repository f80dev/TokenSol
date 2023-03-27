import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {UserService} from "../user.service";

@Component({
  selector: 'app-about',
  templateUrl: './about.component.html',
  styleUrls: ['./about.component.css']
})
export class AboutComponent implements OnInit {

  appname="";

  constructor(public user:UserService) { }

  ngOnInit(): void {
    this.appname=this.user.appname;
  }

}
