import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-mywallet',
  templateUrl: './mywallet.component.html',
  styleUrls: ['./mywallet.component.css']
})
export class MywalletComponent implements OnInit {

  constructor(public user:UserService,public network:NetworkService) { }

  ngOnInit(): void {
    this.user.connect(()=>{});
  }

}
