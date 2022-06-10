import { Component, OnInit } from '@angular/core';
import {Clipboard} from '@angular/cdk/clipboard';
import {MetabossService} from "../metaboss.service";
import {MetabossKey, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";

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
    public clipboard: Clipboard,
    public network:NetworkService,
    public toast:MatSnackBar
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    this.network.wait("Chargement des comptes");
    this.metaboss.keys(this.network.network).subscribe((r)=>{
      this.network.wait("");
      this.keys=r;
    })
  }

  add_key() {
    this.metaboss.add_key({
      name:this.name,
      key:this.privateKey
    }).subscribe(()=>{
      this.refresh();
      this.name="";
    })
  }

  sel_key(name:string) {
    this.metaboss.sel_key(name);
    showMessage(this,name+" sélectionnée");
  }

  del_key(name: string) {
    this.metaboss.del_key(name).subscribe(()=>{
      setTimeout(()=>{this.refresh();},1000);
    });
  }

  encrypt(key: any) {
    this.metaboss.encrypte_key(key.name).subscribe((r:any)=>{
      this.clipboard.copy(key.name+": "+r.encrypt);
      showMessage(this,"La clé est disponible dans le presse papier")
    });
  }
}
