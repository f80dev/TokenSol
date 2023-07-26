import { Component, OnInit } from '@angular/core';
import {Clipboard} from '@angular/cdk/clipboard';
import {
  $$,
  CryptoKey,
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
import {wait_message} from "../hourglass/hourglass.component";
import {get_nfluent_wallet_url} from "../../nfluent";

@Component({
  selector: 'app-keys',
  templateUrl: './keys.component.html',
  styleUrls: ['./keys.component.css']
})
export class KeysComponent implements OnInit {
  privateKey: string="";
  name: string="";
  message="";
  sel_network: any;

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
        let network=environment.networks_available.split(',')[0]
        this.sel_network={label:network,value:network}
        this.network.init_network(network)
      } else {
        this.user.login("Se connecter pour gérer les clés de l'application");
      }
  }

  refresh(){
    this.user.connect().then((profil)=> {

      let op_id= this.operation.sel_ope ? this.operation.sel_ope.id : "";

      this.network.init_keys( true,this.user.profil.access_code, op_id).then(()=>{

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

  encrypt(key: any,encrypt_all=false) {
    this.network.encrypte_key(key.name,this.network.network,this.privateKey).subscribe((r:any)=>{
      if(encrypt_all){
        this.clipboard.copy(key.name+": "+r.encrypt);
      } else {
        this.clipboard.copy(key.name+": "+r.private_key);
      }
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

  open_gallery(key: CryptoKey) {
    this.router.navigate(["gallery"],{queryParams:{
      toolbar:false,
        size:60,
        address:key.address,
        showNfluentWalletConnect:true,
        directShowQRCode:true,
        showWalletConnect:true,
        visual:"https://nfluent.io/assets/paper1.jpg"}})
  }

  open_wallet(key: CryptoKey) {
    this.router.navigate(
      ["wallet"],
      {queryParams:{p:setParams({addr:key.address,toolbar:false,takePhoto:true,network:this.sel_network.value},"","")}}
    );
  }

  // open_lazy_wallet(key: CryptoKey) {
  //   this.router.navigate(
  //     ["wallet"],
  //     {queryParams:{p:setParams({addr:key.address,toolbar:false,takePhoto:true,network:"db-server-nfluent"},"","")}}
  //   );
  // }


  open_extra_wallet(key: CryptoKey) {
    open(get_nfluent_wallet_url(key.address,this.sel_network.value,environment.appli))
  }

  open_collections(key: CryptoKey,tools="nfluent") {
    if(tools=="nfluent" && key){
      this.network.encrypte_key(key.name!,this.sel_network.value,key.secret_key!,key.address).subscribe((r)=>{
        this.router.navigate(["collections"],{queryParams:{owner:key.address,network:this.sel_network.value,encrypted:r.encrypt}});
      })
    }
    if(tools=="inspire")open(this.network.getExplorer(key.address,"accounts"),"explorer");
    if(tools=="opensea")open(this.network.getExplorer(key.address),"explorer");
  }

  open_elrond_wallet() {
    let url="https://wallet.elrond.com/unlock/pem"
    if(this.sel_network.value.indexOf("devnet")>-1)url=url.replace("wallet","devnet-wallet");
    open(url,"elrondwallet")
  }

  open_faucet(key: CryptoKey) {
    showMessage(this,"L'adresse du compte est dans le presse-papier")
    if(this.network.isElrond()){
      open("https://devnet-wallet.multiversx.com/unlock/pem","faucet")
      //TODO ici ajouter l'ouverture du rechargement
    }
    if(this.network.isPolygon()){
      open("https://faucet.polygon.technology/","faucet")
    }
  }

    encrypt_key() {

    }

    async create_key() {
        let email=await _prompt(this,"Créer un nouveau wallet "+this.sel_network.value,this.user.profil.email,
            "Indiquer votre mail pour recevoir la clé privée de votre wallet",
            "text","Créer la clé","Annuler",false);
        if(isEmail(email)){
          this.network.create_account(this.sel_network.value,email).subscribe((r:any)=>{
            this.clipboard.copy(r.secret_key);
            showMessage(this,"Consulter votre mail pour retrouver votre compte, la clé privée est disponible dans le presse papier");
            this.open_faucet(newCryptoKey(r.addr));
          })
        }
    }

  updateNetwork($event: any) {
    this.sel_network=$event;
    this._location.replaceState("keys","network="+this.sel_network.value)
    this.network.init_network(this.sel_network.value)
  }

    async open_nfluent_wallet() {
        let addr=await _prompt(this,"Indiquer une adresse du réseau "+this.sel_network.value,"","","text","Ok","Annuler",false);
        this.router.navigate(["mywallet"],{queryParams:{p:setParams({
              addr:addr,
              toolbar: true,
              network: this.sel_network.value
            },"","")}})
    }

  open_explorer(key: CryptoKey) {
    open(this.network.getExplorer(key.address,"accounts","explorer"),"explorer")
  }

  async burn_all_nft(key: CryptoKey) {
    let rep:any=await _prompt(this,"Bruler tous les NFTs","","","oui/non","Brûler","Annuler",true);
    if(rep=="yes"){
      wait_message(this,"Récupération des NFT de "+key.address)
      let resp=await this.network.get_tokens_from("owner",key.address,100,false,null,0,this.sel_network.value);
      let i=resp.result.length;
      for(let token of resp.result){
        try{
          if(token.supply>0){
            await this.network.burn(token.address,key,this.sel_network.value,1)
          }
        }catch (e) {
          wait_message(this,"Impossible de supprimer "+token.name)
        }

        i=i-1;
        wait_message(this,"Reste "+i+" NFTs a brûler")
      }
      wait_message(this)
    }
  }

  open_airdrop(key: CryptoKey) {
    if(key.secret_key && key.address){
      this.network.encrypte_key(key.name || "",this.sel_network.value,key.secret_key,key.address).subscribe((r:any)=>{
        open("https://airdrop.nfluent.io/?"+setParams({wallet:r.encrypt,network:this.sel_network.value,address:key.address}))
      })
    }
  }
}
