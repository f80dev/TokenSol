import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {Router} from "@angular/router";
import {_prompt} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";

@Component({
  selector: 'app-settings',
  templateUrl: './settings.component.html',
  styleUrls: ['./settings.component.css']
})
export class SettingsComponent implements OnInit {

  constructor(
      public user:UserService,
      public router:Router,
      public dialog:MatDialog
  ) {}

  ngOnInit(): void {
    if (!this.user.isConnected())this.user.login("Veuillez vous connecter pour accèder a vos préférences");
  }

  logout() {
    this.user.logout();
    this.router.navigate(["about"]);
  }

  delete_account() {
    this.user.delete_account().then(()=>{
      this.router.navigate(["login"]);
    })
  }

    change_password() {
        _prompt(this,"Nouveau mot de passe").then((r:string)=>{
          this.user.change_access_code(r);
        })
    }
}
