import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {getParams, newCryptoKey, now, showError, showMessage} from "../../tools";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {wait_message} from "../hourglass/hourglass.component";
import {_ask_for_paiement} from "../ask-for-payment/ask-for-payment.component";
import {environment} from "../../environments/environment";
import {MatDialog} from "@angular/material/dialog";

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

  addr:string="";
  perms: any;
  types_collection=[{label:"Non fongible",value:"NonFungibleESDT"},{label:"Semi Fongible",value:"SemiFungibleESDT"}];
  collections: Collection[]=[]
  miner: any;

  constructor(
    public network:NetworkService,
    public router:Router,
    public user:UserService,
    public toast:MatSnackBar,
    public _location:Location,
    public routes:ActivatedRoute,
    public dialog:MatDialog
  ) {}


  async ngOnInit() {
    let params:any=await getParams(this.routes);
    this.refresh(params["owner"],params["network"]);
  }


  refresh(addr:string,network:string){
    if(addr && network){
      this.addr=addr;
      this.message="Récupération des collections";
      this.network.get_account(addr,network).subscribe((accounts:any[])=>{
        this.miner=accounts[0];
      })

      this.network.get_collections(addr,network,true).subscribe((r:any)=>{
        this.message="";
        this.collections=[];
        for(let col of r){
          if(col.roles){
            for(let r of col.roles){
              delete r.roles;
            }
          }
          this.collections.push(col);
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



  async create_collection() {
    this.new_collection.owner=this.miner;
    if(!this.new_collection.name || this.new_collection.name.length<3 || this.new_collection.name?.indexOf(' ')>-1){
      showMessage(this,"Format du nom incorrect");
      return;
    }
    this.network.create_collection(this.new_collection,true).subscribe(async (r:any)=>{
      let rep:any=await _ask_for_paiement(this,this.user.merchant.wallet?.token!,
          environment.collection_cost.price_in_crypto,
          environment.collection_cost.price_in_fiat,
          this.user.merchant!,
          this.user.wallet_provider,
          "Confirmer le création de la collection",
          "",
          "",
          this.user.profil.email,
          {contact: "contact@nfluent.io", description: "Création d'une collection NFT pour "+this.network.network.split("-")[0], subject: "Création d'une nouvelle collection"},
          this.user.buy_method)

      if(rep){
        this.user.init_wallet_provider(rep.data.provider);
        this.user.buy_method=rep.buy_method;

        showMessage(this,"Lancement du processus de minage");

        // if(!this.user.key?.privatekey){
        //   for(let k of this.network.keys){
        //     if(k.address==this.user.addr){
        //       this.user.key=k;
        //     }
        //   }
        // }
        //

        wait_message(this,"Fabrication de la collection sur la blockchain");
        this.network.create_collection(this.new_collection).subscribe((r:any)=>{
          this.collections.splice(0,0,r.collection);
          wait_message(this)
          showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
        },(err)=>{
          this.network.wait();
          showError(this,err);
        })
      }
    })





  }



  open_inspire() {
    open(this.network.getExplorer(this.addr),"Explorer");
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
