import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute} from "@angular/router";
import {showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-collections',
  templateUrl: './collections.component.html',
  styleUrls: ['./collections.component.css']
})
export class CollectionsComponent implements OnInit {
  addr:string="";
  new_collection:Collection = {
    description: "description",
    id: undefined,
    name: "son nom",
    owner: undefined,
    price: undefined,
    type: undefined,
    visual: undefined
  };

  constructor(
    public network:NetworkService,
    public toast:MatSnackBar,
    public routes:ActivatedRoute,
    public user:UserService
  ) { }

  ngOnInit(): void {
      this.routes.queryParams.subscribe((params:any)=>{
        if(params.hasOwnProperty("owner")){
          this.addr=params["owner"]
          this.user.init(this.addr);
        } else {
          this.addr=this.user.addr;
        }
        this.refresh(this.addr)
      })
  }

  refresh(addr=""){
    this.network.get_collections(addr).subscribe((r:any)=>{
      this.user.collections=r;
    })
  }

  open_collection(col: Collection) {
    if(this.network.isElrond())
      open("https://"+(this.network.isMain() ? "" : "devnet.")+"inspire.art/collections/"+col.id);
  }

  create_collection() {
    if(!this.new_collection.name || this.new_collection.name.length<3 || this.new_collection.name?.indexOf(' ')>-1){
      showMessage(this,"Format du nom incorrect");
      return;
    }
    this.network.wait("Fabrication de la collection sur la blochain")
    this.network.create_collection(this.user.addr,this.new_collection).subscribe((r:any)=>{
      this.user.collections.push(r.collection);
      showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
    })
  }

  open_inspire() {
    open("https://"+(this.network.isMain() ? "" : "devnet.")+"inspire.art/"+this.addr+"/collections");
  }
}
