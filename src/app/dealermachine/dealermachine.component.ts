import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {showMessage} from "../../tools";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";

  constructor(
    public routes:ActivatedRoute,
    public network:NetworkService,
    public router:Router
  ) { }

  ngOnInit(): void {

  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";

  valide() {
    let id=this.routes.snapshot.queryParamMap.get("id");
    let ope=this.routes.snapshot.queryParamMap.get("ope");
    if(id){
      if(this.address.indexOf("@")>4){
        this.network.send_confirmation(this.address,id).subscribe(()=>{});
       } else {
        if(this.address.length>20){
          this.message="Demande en cours";
          this.network.mint_for_contest(this.address,id,ope!).subscribe(()=>{
            showMessage(this,"Vous avez gagné un nouveau NFT");
            this.message="";
            this.router.navigate(["contest"],{queryParams:{ope:ope}})
          },(err)=>{
            showMessage(this,"Vous vous êtes fais doublé ! Retentez votre chance")
            this.message="";
          })
        }
      }

    }

  }
}
