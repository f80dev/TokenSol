import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {showMessage} from "../../tools";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-collections',
  templateUrl: './collections.component.html',
  styleUrls: ['./collections.component.css']
})
export class CollectionsComponent implements OnInit {
  new_collection:Collection = {
    description: "description",
    id: undefined,
    name: "MaCollection",
    owner: undefined,
    price: undefined,
    type: undefined,
    visual: undefined,
    link: ""
  };

  constructor(
    public network:NetworkService,
    public router:Router,
    public toast:MatSnackBar,
    public _location:Location,
    public routes:ActivatedRoute,
    public user:UserService
  ) {}

  ngOnInit(): void {
    this.routes.queryParams.subscribe((params:any)=>{
      if(params.hasOwnProperty("owner")){
        this.user.addr=params["owner"]
        this.user.init(this.user.addr);
      }
    })

    this.user.addr_change.subscribe((addr)=>{
      this.refresh(addr);
    })
  }

  refresh(addr=""){
    this.network.wait("Récupération des collections");
    this._location.replaceState("./collections","owner="+addr);
    this.network.get_collections(addr).subscribe((r:any)=>{
      this.network.wait();
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
      this.network.wait();
      showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
    })
  }



  open_inspire() {
    open("https://"+(this.network.isMain() ? "" : "devnet.")+"inspire.art/"+this.user.addr+"/collections");
  }

  open_miner(col: Collection) {
    this.router.navigate(["miner"],{queryParams:{collection:col.id}})
  }

  open_explorer(col:Collection) {
    https://devnet-explorer.elrond.com/collections/
    open("https://"+(this.network.isMain() ? "" : "devnet")+"-explorer.elrond.com/collections/"+col.id);
  }

  open_analyser(col: Collection) {
    this.router.navigate(["analytics"],{queryParams:{collection:col.id}});
  }
}
