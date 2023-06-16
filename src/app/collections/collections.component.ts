import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Collection} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {$$, CryptoKey, getParams, newCryptoKey, now, setParams, showError, showMessage} from "../../tools";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {wait_message} from "../hourglass/hourglass.component";
import {_ask_for_paiement} from "../ask-for-payment/ask-for-payment.component";
import {environment} from "../../environments/environment";
import {MatDialog} from "@angular/material/dialog";
import {NFT} from "../../nft";
import {_prompt} from "../prompt/prompt.component";
import {Clipboard} from "@angular/cdk/clipboard";

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
    gallery:true,
    name: "MaCollection",
    owner: newCryptoKey(),
    price: undefined,
    type: "NonFungibleESDT",
    visual: undefined,
    roles: [],
    supply: 1,
    link: "",
    options: this.collection_options.map((x:any)=>{return x.value})
  };

  perms: any;
  types_collection=[{label:"Non fongible",value:"NonFungibleESDT"},{label:"Semi Fongible",value:"SemiFungibleESDT"}];
  collections: Collection[]=[]
  miner: CryptoKey | undefined;
  preview_nfts: NFT[]=[];
  params: any={}

  constructor(
    public network:NetworkService,
    public router:Router,
    public clipboard:Clipboard,
    public user:UserService,
    public toast:MatSnackBar,
    public _location:Location,
    public routes:ActivatedRoute,
    public dialog:MatDialog
  ) {
    $$("Inscription à la modification des parametres")
    this.user.params_available.subscribe((params:any)=>{
      this.params=params;
      if(this.collections.length==0){
        this.refresh(params["owner"],params["network"]);
      }
    })
  }

  async ngOnInit() {
    let params:any=await getParams(this.routes);
    this.params=params;
    this.refresh(params.owner,params.network);
  }

  local_save(){

  }


  refresh(addr:string,network:string,with_detail=true){
    if(addr && network){
      this.network.network=network;
      this.message="Récupération des collections";
      this.network.get_account(addr,network).subscribe((accounts:any[])=>{
        this.miner=accounts[0];
      })

      this.network.get_collections(addr,network,with_detail).subscribe((r:any)=>{
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
    if(this.network.isBlockchain()){
      open(this.network.getExplorer(col.id),"Explorer");
    } else {
      this.network.get_nfts_from_collection(col.id,this.network.network).subscribe((result)=>{
        this.preview_nfts=result.nfts;
        if(this.preview_nfts.length==0)showMessage(this,"Aucun NFT dans cette collection")
      })
    }

  }



  async create_collection() {
    if(this.miner){
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
          if(rep.data){
            this.user.init_wallet_provider(rep.data.provider);
            this.user.buy_method=rep.buy_method;
          }

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
            this.refresh(this.miner!.address,this.network.network)
            wait_message(this)
            showMessage(this,"Votre collection est créé pour "+r.cost+" egld");
          },(err)=>{
            this.network.wait();
            showError(this,err);
          })
        }
      },(err)=>{
        this.network.wait();
        showError(this,err);
      })
    }
  }



  open_inspire() {
    if(this.miner)open(this.network.getExplorer(this.miner.address),"Explorer");
  }


  open_miner(col: Collection) {
    this.router.navigate(["miner"],{queryParams:{collection:col.id,owner:this.miner,network:this.network.network}})
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

  open_dealer(col: Collection,store_type="dispenser") {
    this.network.encrypte_key("",this.network.network,this.miner!.secret_key!).subscribe(async (r)=>{
      let params_dest:any=await _prompt(this,"Paramètres de la destinations",localStorage.getItem("params_dest") || "","clé du mineur, blockchain et collection","text","Ok","Annuler",false);
      if(!params_dest)return;
      localStorage.setItem("params_dest",params_dest)

      params_dest=JSON.parse(params_dest)

      let params={
        network:this.network.network,
        collection:col.id,
        miner:r.encrypt,
        networks:this.network.networks_available.join(","),
        miner_dest:params_dest.miner_dest,
        network_dest:params_dest.network_dest,
        collection_dest:params_dest.collection_dest,
        miner_addr:r.address,
        toolbar:false
      }
      this.router.navigate([store_type], {queryParams:{p:setParams(params,"","")}})
    })

  }

  copy_parameters(col: Collection) {

      let rc={
        miner_dest:this.params.encrypted,
        network_dest:this.network.network,
        collection_dest:col.id
      }
      if(this.clipboard.beginCopy(JSON.stringify(rc)).copy()){
        showMessage(this,"Les parametres de la collection sont disponibles dans le presse papier")
      }


  }

  async add_validator(col: Collection) {
    let rep=await _prompt(this,"Tester un validateur","fictif","Nom du validateur","text","Tester","Annuler",false)
    open(environment.appli+"/autovalidate?name="+rep+"&network="+this.network.network+"&collection="+col.id)
    this.router.navigate(["validators"])
  }

  async short_url(col: Collection) {
    let redirect=await _prompt(this,"Lien de redirection","","commençant par https","text","Réduire","Annuler",false)
    let domain=encodeURIComponent("https://s.f80.fr")
    open("https://s.f80.fr/create/?redirect="+decodeURIComponent(redirect)+"&collection="+col.id+"&domain="+domain)
  }
}
