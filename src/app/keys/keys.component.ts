import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {MetabossService} from "../metaboss.service";
import {MetabossKey, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-keys',
  templateUrl: './keys.component.html',
  styleUrls: ['./keys.component.css']
})
export class KeysComponent implements OnInit {
  privateKey: string="";
  name: string="";
  keys: MetabossKey[] = [];

  constructor(
    public metaboss:MetabossService,
    public toast:MatSnackBar
  ) { }

  ngOnInit(): void {
    this.metaboss.keys().subscribe((r)=>{this.keys=r;})
  }

  add_key() {
    this.metaboss.add_key({
      name:this.name,
      key:this.privateKey
    }).subscribe(()=>{
      this.sel_key(this.name);
      this.name="";
    })
  }

  sel_key(name:string) {
    this.metaboss.sel_key(name);
    showMessage(this,name+" sélectionnée");
  }

}
