import { Component, OnInit } from '@angular/core';
import {Location} from "@angular/common";
import {UserService} from "../user.service";


@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
export class LoginComponent implements OnInit {


  constructor(
    public _location:Location,
    public user:UserService
  ) { }

  ngOnInit(): void {
  }

  authent($event: { strong: boolean; nftchecked: boolean; address: string }) {
    if($event.strong){
      this.user.init($event.address).then(()=>{
        this._location.back();
      });
    }
  }
}
