import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {getParams, newCryptoKey, showError, showMessage} from "../../tools";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {wait_message} from "../hourglass/hourglass.component";

@Component({
  selector: 'app-collections',
  templateUrl: './collections.component.html',
  styleUrls: ['./collections.component.css']
})
export class CollectionsComponent implements OnInit {
  message="";

  //voir https://docs.elrond.com/tokens/nft-tokens/
  collection_options=[
    {label:"Freezable",value:"canFreeze"},
    {label:"Wipeable",value:"canWipe"},
    {label:"Pausable",value:"canPause"},
    {label:"Délégation de minage",value:"canTransferNFTCreateRole"},
    {label:"Transférable",value:"canChangeOwner"},
    {label:"Modifiable",value:"canUpgrade"},
    {label:"Role spéciaux",value:"canAddSpecialRoles"},
  ]

  new_collection:Collection = {
    description: "description",
    id: "",
    name: "MaCollection",
    owner: newCryptoKey(),
    price: undefined,
    type: "NonFungibleESDT",
    visual: undefined,
    roles: [],
    link: "",
    options: this.collection_options.map((x:any)=>{return x.value})
  };


  perms: any;
  types_collection=[{label:"Non fongible",value:"NonFungibleESDT"},{label:"Semi Fongible",value:"SemiFungibleESDT"}];

  constructor(
    public network:NetworkService,
    public router:Router,
    public toast:MatSnackBar,
    public _location:Location,
    public routes:ActivatedRoute,
    public user:UserService
  ) {}


  ngOnInit(): void {
    getParams(this.routes).then(async (params:any)=>{
      let owner=params["owner"] || this.user.addr
      let network=params["network"] || this.network.network
      let r=await this.user.init(owner,network);
      this.refresh(this.user.addr,this.network.network);
    })
    this.user.addr_change.subscribe((addr)=>{this.refresh(addr,this.network.network);})
    this.network.network_change.subscribe((new_network)=>{this.refresh(this.user.addr,this.network.network);})
  }


  refresh(addr:string,network:string){
    if(addr && network){
      this._location.replaceState("./collections","owner="+addr+"&network="+network);
      this.message="Récupération des collections";
      this.network.get_collections(addr,network,true).subscribe((r:any)=>{
        this.message="";
        this.user.collections=[];
        for(let col of r){
          if(col.roles){
            for(let r of col.roles){
              delete r.roles;
            }
          }
          this.user.collections.push(col);
        }
      },(error:any)=>{
        this.network.wait();
        showError(this,error);
      })
    }
  }



  open_collection(col: Collection) {
    open(this.network.getExplorer(col.id),"Explorer");
  }



  create_collection() {
    if(this.user.balance==0){
      showMessage(this,"Solde insuffisant pour créer une collection")
      return;
    }
    if(!this.user.key?.privatekey){
      for(let k of this.network.keys){
        if(k.address==this.user.addr){
          this.user.key=k;
        }
      }
    }
    if(this.user.key)this.new_collection.owner=this.user.key;

    if(!this.new_collection.name || this.new_collection.name.length<3 || this.new_collection.name?.indexOf(' ')>-1){
      showMessage(this,"Format du nom incorrect");
      return;
    }
    wait_message(this,"Fabrication de la collection sur la blockchain");
    this.network.create_collection(this.new_collection).subscribe((r:any)=>{
      this.user.collections.splice(0,0,r.collection);
      wait_message(this)
      showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
    },(err)=>{
      this.network.wait();
      showError(this,err);
    })
  }



  open_inspire() {
    open(this.network.getExplorer(this.user.addr),"Explorer");
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

  create_with_wallet_elrond(){
    open("https://wallet.multiversx.com/issue-nft/create-collection")
  }


}
