import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";

@Component({
  selector: 'app-intro',
  templateUrl: './intro.component.html',
  styleUrls: ['./intro.component.css']
})
export class IntroComponent implements OnInit {
  appname: any;
  version: any;

  constructor() {
    this.appname=environment.appname;
    this.version=environment.version;
  }

  ngOnInit(): void {
  }

}
