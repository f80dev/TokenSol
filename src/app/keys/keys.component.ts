import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";

@Component({
  selector: 'app-keys',
  templateUrl: './keys.component.html',
  styleUrls: ['./keys.component.css']
})
export class KeysComponent implements OnInit {
  privateKey: string="";
  name: string="";

  constructor(
    public user:UserService
  ) { }

  ngOnInit(): void {

  }

  add_key() {
    this.user.add_key({
      name:this.name,
      key:this.privateKey
    })
  }
}
