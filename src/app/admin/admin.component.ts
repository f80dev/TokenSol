import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
//test http://127.0.0.1:4200/admin
export class AdminComponent implements OnInit {

  constructor(
    public user:UserService
  ) { }

  ngOnInit(): void {
    this.user.login();
  }

}
