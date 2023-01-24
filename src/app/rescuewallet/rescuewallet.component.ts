import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {$$, getParams, showMessage} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {Operation} from "../../operation";

@Component({
  selector: 'app-rescuewallet',
  templateUrl: './rescuewallet.component.html',
  styleUrls: ['./rescuewallet.component.css']
})
export class RescuewalletComponent implements OnInit {
  email="";
  db="db-server-nfluent";
  message: string="";

  constructor(
      public network:NetworkService,
      public toast:MatSnackBar,
      public routes:ActivatedRoute
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.network.network=params["network"] || "elrond-devnet";
      this.db=params["db"];
      if(!this.db){
        this.network.get_operations(params["ope"] || params["operation"]).subscribe((operation:Operation)=>{
          this.db="db-"+operation.database?.connexion+"-"+operation.database?.dbname;
          $$("Utilisation de "+this.db+" pour la gestion des emails");
        });
      }
    })
  }


  ask_rescue() {
    if(this.email){
      this.network.rescue_wallet(this.email,this.db,this.network.network).subscribe((result:any)=>{
        this.message=result.message;
        showMessage(this,result.message)
      })
    }
  }

  retry() {
    this.message="";
    this.email="";
  }
}
