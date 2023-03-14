import { Component, OnInit } from '@angular/core';
import {Clipboard} from '@angular/cdk/clipboard';
import {$$, CryptoKey, getParams, isEmail, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Location} from "@angular/common";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {ActivatedRoute, Router} from "@angular/router";
import {NFLUENT_WALLET} from "../../definitions";
import {OperationService} from "../operation.service";
import {DeviceService} from "../device.service";

@Component({
  selector: 'app-keys',
  templateUrl: './keys.component.html',
  styleUrls: ['./keys.component.css']
})
export class KeysComponent implements OnInit {
  privateKey: string="";
  name: string="";

  constructor(
    public dialog:MatDialog,
    public clipboard: Clipboard,
    public router:Router,
    public network:NetworkService,
    public toast:MatSnackBar,
    public user:UserService,
    public device:DeviceService,
    public operation:OperationService,
    public _location:Location,
    public routes:ActivatedRoute
  ) {
    this.network.network_change.subscribe(()=>{this.refresh();})
    this.operation.sel_ope_change.subscribe(()=>{this.refresh()});
  }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("network"))this.network.network=params["network"];
      if(this.user.isConnected(true)){
          this.refresh();
      } else {
        this.user.login("Se connecter pour gérer les clés de l'application");
      }
    })
  }

  refresh(){
    this.user.connect().then((profil)=> {
      this.network.init_keys(
          this.network.network,
          true,
          this.user.profil.access_code,
          this.operation.sel_ope!.id
      ).then(()=>{
        this.network.wait();
      });
    });
  }


  del_key(name: string) {
    _prompt(this,"Supprimer une clé","","Etes vous sur de vouloir détruire la clé "+name,"","Je suis sûr","Annuler",true).then(()=>{
      this.network.del_key(name).subscribe(()=>{
        setTimeout(()=>{this.refresh();},1000);
      });
    })
  }

  encrypt(key: any) {
    this.network.encrypte_key(key.name,this.network.network,this.privateKey).subscribe((r:any)=>{
      this.clipboard.copy(key.name+": "+r.encrypt);
      showMessage(this,"La clé est disponible dans le presse papier")
    });
  }

  onuploaded_key_file($event: any) {
    let content=atob($event.file.split("base64,")[1]);
    let name=$event.filename.split(".")[0]
    $$("Upload de "+name);
      this.network.add_key({name:name, key:content}).subscribe(()=>{
        showMessage(this,name+" importé");
      })
    }

  new_key() {
    _prompt(this,"Recevoir les informations de votre compte via mail",).then(resp=>{
      if(!resp)resp="";
      let obj={name:this.name, key:this.privateKey,access_code:this.user.profil.access_code,email:resp}
      this.network.add_key(obj).subscribe(()=>{
        this.refresh();
        this.name="";
      })
    })
  }

  open_wallet(key: CryptoKey) {
    this.router.navigate(
      ["wallet"],
      {queryParams:{param:setParams({addr:key.address,toolbar:false,takePhoto:true,network:this.network.network},"","")}}
    );
  }

  open_lazy_wallet(key: CryptoKey) {
    this.router.navigate(
      ["wallet"],
      {queryParams:{param:setParams({addr:key.address,toolbar:false,takePhoto:true,network:"db-server-nfluent"},"","")}}
    );
  }

  open_extra_wallet(key: CryptoKey) {
    open(NFLUENT_WALLET+"/?"+setParams({addr:key.address,toolbar:false,takePhoto:true,network:this.network.network}))
  }

  open_collections(key: CryptoKey,tools="nfluent") {
    if(tools=="nfluent")this.router.navigate(["collections"],{queryParams:{owner:key.address}});
    if(tools=="inspire")open(this.network.getExplorer(key.address),"Explorer");
  }

  open_elrond_wallet() {
    let url="https://wallet.elrond.com/unlock/pem"
    if(this.network.network.indexOf("devnet")>-1)url=url.replace("wallet","devnet-wallet");
    open(url,"elrondwallet")
  }

  open_faucet(key: CryptoKey) {
    showMessage(this,"L'adresse du compte est dans le presse-papier")
    if(this.network.isElrond()){
      debugger
      //TODO ici ajouter l'ouverture du rechargement
    }
    if(this.network.isPolygon()){
      open("https://faucet.polygon.technology/","faucet")
    }
  }

    encrypt_key() {


    }

    async create_key() {
        let email=await _prompt(this,"Créer un nouveau wallet "+this.network.network,"@gmail.com",
            "Indiquer votre mail pour recevoir la clé privée de votre wallet",
            "text","Créer la clé","Annuler",false);
        if(isEmail(email)){
          this.network.create_account(this.network.network,email).subscribe((r:any)=>{
            showMessage(this,"Consulter votre mail pour retrouver votre compte");
            open(r.explorer,"Explorer");
          })
        }
    }
}
