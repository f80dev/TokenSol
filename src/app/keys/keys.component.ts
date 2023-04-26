import { Component, OnInit } from '@angular/core';
import {Clipboard} from '@angular/cdk/clipboard';
import {
  $$,
  CryptoKey,
  get_nfluent_wallet_url,
  getParams,
  isEmail,
  newCryptoKey,
  setParams,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Location} from "@angular/common";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {ActivatedRoute, Router} from "@angular/router";
import {OperationService} from "../operation.service";
import {DeviceService} from "../device.service";
import {environment} from "../../environments/environment";

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

  }

  ngOnInit(): void {
      if(this.user.isConnected()){

      } else {
        this.user.login("Se connecter pour gérer les clés de l'application");
      }
  }

  refresh(){
    this.user.connect().then((profil)=> {

      let op_id= this.operation.sel_ope ? this.operation.sel_ope.id : "";

      this.network.init_keys(this.network.network, true,this.user.profil.access_code, op_id).then(()=>{

          this.network.wait();
          // this.network.network_change.subscribe(()=>{this.refresh();})
          // this.operation.sel_ope_change.subscribe(()=>{this.refresh()});
      });
    });
  }


  del_key(name: string | null) {
    if(name){
      _prompt(this,"Supprimer une clé","","Etes vous sur de vouloir détruire la clé "+name,"","Je suis sûr","Annuler",true).then(()=>{
        this.network.del_key(name).subscribe(()=>{
          setTimeout(()=>{this.refresh();},1000);
        });
      })
    }
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
      {queryParams:{p:setParams({addr:key.address,toolbar:false,takePhoto:true,network:this.network.network},"","")}}
    );
  }

  open_lazy_wallet(key: CryptoKey) {
    this.router.navigate(
      ["wallet"],
      {queryParams:{p:setParams({addr:key.address,toolbar:false,takePhoto:true,network:"db-server-nfluent"},"","")}}
    );
  }

  open_extra_wallet(key: CryptoKey) {
    open(get_nfluent_wallet_url(key.address,this.network.network,environment.appli))
  }

  open_collections(key: CryptoKey,tools="nfluent") {
    if(tools=="nfluent")this.router.navigate(["collections"],{queryParams:{owner:key.address,network:this.network.network}});
    if(tools=="inspire")open(this.network.getExplorer(key.address),"Explorer");
    if(tools=="opensea")open(this.network.getExplorer(key.address),"Explorer");
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
        let email=await _prompt(this,"Créer un nouveau wallet "+this.network.network,this.user.profil.email,
            "Indiquer votre mail pour recevoir la clé privée de votre wallet",
            "text","Créer la clé","Annuler",false);
        if(isEmail(email)){
          this.network.create_account(this.network.network,email).subscribe((r:any)=>{
            this.clipboard.copy(r.secret_key);
            showMessage(this,"Consulter votre mail pour retrouver votre compte, la clé privée est disponible dans le presse papier");
            this.open_faucet(newCryptoKey(r.addr));
          })
        }
    }

  updateNetwork($event: any) {
    this.network.network=$event;
    this._location.replaceState("keys","network="+this.network.network)
  }

    async open_nfluent_wallet() {
        let addr=await _prompt(this,"Indiquer une adresse du réseau "+this.network.network,"","","text","Ok","Annuler",false);
        this.router.navigate(["mywallet"],{queryParams:{p:setParams({
              addr:addr,
              toolbar: true,
              network: this.network.network
            },"","")}})
    }
}
