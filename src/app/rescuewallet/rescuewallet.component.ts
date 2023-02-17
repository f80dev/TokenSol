import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {$$, getParams, showMessage} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {Operation} from "../../operation";

//Ce module permet la récupération des wallet via l'adresse mail. Il repose sur une base de données ou les adresse mails sont cryptées
//Il peut être mise en place sur un site web

@Component({
  selector: 'app-rescuewallet',
  templateUrl: './rescuewallet.component.html',
  styleUrls: ['./rescuewallet.component.css']
})
export class RescuewalletComponent implements OnInit {
  @Input() email="";
  @Input() db="db-server-nfluent";
  message: string="";
  @Input() network_name="";
  @Output("validate") onvalidate:EventEmitter<any>=new EventEmitter();
  @Input() intro="Indiquer votre adresse email pour recevoir un lien vers votre wallet";

  constructor(
      public network:NetworkService,
      public toast:MatSnackBar,
      public routes:ActivatedRoute
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("network")){
        this.network_name=params["network"] || "elrond";
        this.db=params["db"];
        if(!this.db){
          this.network.get_operations(params["ope"] || params["operation"]).subscribe((operation:Operation)=>{
            this.db="db-"+operation.database?.connexion+"-"+operation.database?.dbname;
            $$("Utilisation de "+this.db+" pour la gestion des emails");
          });
        }
      }
    })
  }


  ask_rescue() {
    if(this.email){
      this.network.rescue_wallet(this.email,this.db,this.network_name).subscribe((result:any)=>{
        this.message=result.message;
        showMessage(this,result.message)
        this.onvalidate.emit(result.message);
      })
    }
  }

  retry() {
    this.message="";
    this.email="";
  }
}
