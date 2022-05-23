import { Component, OnInit } from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";
  wallet_link: string="";
  nft:any={};

  constructor(
    public routes:ActivatedRoute,
    public network:NetworkService,
    public toast:MatSnackBar,
    public router:Router
  ) { }

  ngOnInit(): void {
    this.network.get_nft_from_db(this.routes.snapshot.queryParamMap.get("id") || "").subscribe((nft:any)=>{
      this.nft=nft || {};
      if(!nft){
        this.lost();
      }
    })
  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";

  lost(ope:any=null){
    showMessage(this,"Vous vous êtes fais doublé ! Retentez votre chance")
    this.message="";
    if(ope)this.router.navigate(ope.redirect.win);
  }

  valide() {
    let id=this.routes.snapshot.queryParamMap.get("id");
    if(id){
      if(this.address.length>5){
        this.message="Demande en cours";
        this.network.mint_for_contest(this.address,id).subscribe((r:any)=>{
          showMessage(this,"Vous avez gagné un nouveau NFT");
          this.wallet_link=r.wallet_link;
          this.message="";
          this.router.navigate(r.ope.redirect.win);
        },(err)=>{
          this.lost();
        })
      }
    }

  }
}
