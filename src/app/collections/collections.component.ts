import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {showError, showMessage} from "../../tools";
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
    id: "",
    name: "MaCollection",
    owner: undefined,
    price: undefined,
    type: undefined,
    visual: undefined,
    roles: [],
    link: "",
    options:{
      canWipe:true,
      canTransferNFTCreateRole:true,
      canUpgrade:true,
      canPause:true,
      canFreeze:true,
      canChangeOwner:true,
      canAddSpecialRoles:true
    }
  };


  //voir https://docs.elrond.com/tokens/nft-tokens/
  collection_options=[
    {label:"Freezable",name:"canFreeze",value:true},
    {label:"Wipeable",name:"canWipe",value:true},
    {label:"Pausable",name:"canPause",value:true},
    {label:"Délégation de minage",name:"canTransferNFTCreateRole",value:true},
    {label:"Transférable",name:"canChangeOwner",value:true},
    {label:"Modifiable",name:"canUpgrade",value:true},
    {label:"Role spéciaux",name:"canAddSpecialRoles",value:true},
  ]
  perms: any;


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

    this.network.network_change.subscribe((new_network)=>{
      this.refresh(this.user.addr);
    })

    if(this.user.addr)this.refresh();
  }



  refresh(addr=""){
    this.network.wait("Récupération des collections");
    this._location.replaceState("./collections","owner="+addr);
    this.network.get_collections(addr,this.network.network,true).subscribe((r:any)=>{
      this.network.wait();
      this.user.collections=[];
      for(let col of r){
        for(let r of col.roles){
          delete r.roles;
        }
        this.user.collections.push(col);
      }
    })
  }



  open_collection(col: Collection) {
    this.network.open_gallery(col.id);
  }



  create_collection() {
    if(this.user.balance==0){
      showMessage(this,"Solde insuffisant pour créer une collection")
      return;
    }

    if(!this.new_collection.name || this.new_collection.name.length<3 || this.new_collection.name?.indexOf(' ')>-1){
      showMessage(this,"Format du nom incorrect");
      return;
    }
    this.network.wait("Fabrication de la collection sur la blochain")
    for(let col of this.collection_options){
      if(col.name){ // @ts-ignore
        this.new_collection.options[col.name]=col.value;
      }
    }
    this.network.create_collection(this.user.addr,this.new_collection).subscribe((r:any)=>{
      this.user.collections.splice(0,0,r.collection);
      this.network.wait();
      showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
    },(err)=>{
      this.network.wait();
      showError(this,err);
    })
  }



  open_inspire() {
    this.network.open_gallery(this.user.addr);
  }



  open_miner(col: Collection) {
    this.router.navigate(["miner"],{queryParams:{collection:col.id,owner:this.user.addr}})
  }



  open_explorer(col:Collection) {
    //https://devnet-explorer.elrond.com/collections/
    open("https://"+(this.network.isMain() ? "" : "devnet-")+"explorer.elrond.com/collections/"+col.id);
  }

  open_analyser(col: Collection) {
    this.router.navigate(["analytics"],{queryParams:{collection:col.id}});
  }

  set_roles(col: Collection) {
    if(col && col.id){
      this.network.set_role(col.id,this.user.addr,this.network.network).subscribe(()=>{
        showMessage(this,"role affected");
      })
    }

  }

  has_perm(col: Collection, address: string, perm: any) {
    // if(col.roles){
    //   for(let role of col.roles){
    //
    //   }
    // }
    return "checked";

  }


}
