import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";
import {Token} from "../nfts/nfts.component";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-validate',
  templateUrl: './validate.component.html',
  styleUrls: ['./validate.component.css']
})
export class ValidateComponent implements OnInit {

  operation: string ="calvi2022";
  query: string="";
  tokens:Token[]=[];
  message="";

  constructor(public routes:ActivatedRoute,
              public network:NetworkService,
              public _location:Location,
              public toast:MatSnackBar,
              public alias:AliasPipe
  ) { }

  ngOnInit(): void {
    this.operation=this.routes.snapshot.queryParamMap.get("operation") || "calvi2022";
    this.query=this.routes.snapshot.queryParamMap.get("q") || "";
    setTimeout(()=>{this.update_token(this.query);},1500);

  }

  search(query:string){
    this.network.isValideToken("calvi2022",query).subscribe((r:any)=>{

    })
  }

  update_model($event:any) {
    //if(this.query.length>5)this.search(this.query);
    this.update_token($event);
  }

  update_token(address:string){
    if(address.length==0)return;
    let addr=this.alias.transform(address,"pubkey");
    this.message="Recherche des NFTs";
    this.network.get_tokens_from("owner",addr).then((r:any[])=>{
      this.message="";
      this._location.replaceState("./validate/?q="+this.query);
      for(let t of r){
        let token:Token=t;
        this.tokens.push(token);
      }
    },(err)=>{
      showError(this)
    })
  }

  onflash($event: any) {
    let addr=$event;
    this.update_token(addr);
  }
}
