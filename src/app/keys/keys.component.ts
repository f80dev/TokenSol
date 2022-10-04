import { Component, OnInit } from '@angular/core';
import {Clipboard} from '@angular/cdk/clipboard';
import {MetabossService} from "../metaboss.service";
import {$$, CryptoKey, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {Location} from "@angular/common";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {Router} from "@angular/router";
import {NFLUENT_WALLET} from "../../definitions";

@Component({
  selector: 'app-keys',
  templateUrl: './keys.component.html',
  styleUrls: ['./keys.component.css']
})
export class KeysComponent implements OnInit {
  privateKey: string="";
  name: string="";

  constructor(
    public metaboss:MetabossService,
    public dialog:MatDialog,
    public clipboard: Clipboard,
    public router:Router,
    public network:NetworkService,
    public toast:MatSnackBar,
    public user:UserService,
    public _location:Location
  ) { }

  ngOnInit(): void {
    if(this.user.isConnected(true)){
      this.refresh();
    } else {
      this.user.login();
    }
  }

  refresh(){
    this.user.connect().then((profil)=> {
      this.metaboss.init_keys(this.network.network,true).then(()=>{this.network.wait();});
    });
  }

  add_key() {
    this.metaboss.add_key({name:this.name, key:this.privateKey
    }).subscribe(()=>{
      this.refresh();
      this.name="";
    })
  }

  sel_key(name:string) {
    this.metaboss.sel_key(name);
    showMessage(this,name+" sélectionnée");
  }

  del_key(name: string) {
    this.metaboss.del_key(name).subscribe(()=>{
      setTimeout(()=>{this.refresh();},1000);
    });
  }

  encrypt(key: any) {
    this.metaboss.encrypte_key(key.name).subscribe((r:any)=>{
      this.clipboard.copy(key.name+": "+r.encrypt);
      showMessage(this,"La clé est disponible dans le presse papier")
    });
  }

  onuploaded_key_file($event: any) {
    let content=atob($event.file.split("base64,")[1]);
    let name=$event.filename.split(".")[0]
    $$("Upload de "+name);
      this.metaboss.add_key({name:name, key:content}).subscribe(()=>{
        showMessage(this,name+" importé");
      })
    }

  new_key() {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Recevoir les informations de votre compte via mail",
          placeholder: "Saisissez votre adresse mail",
          type: "text",
          onlyConfirm:false,
          lbl_ok:"Recevoir par mail",
          lbl_cancel:"Ne pas recevoir"
        }
    }).afterClosed().subscribe(resp => {
      if(!resp)resp="";
      this.metaboss.add_key({name:this.name},this.network.network,resp).subscribe((key:any)=>{
        this.refresh();
      })
    });

  }

  open_wallet(key: CryptoKey) {
    this.router.navigate(
      ["wallet"],
      {queryParams:{param:setParams({addr:key.pubkey,toolbar:false,takePhoto:true,network:this.network.network})}}
    );
  }

  open_extra_wallet(key: CryptoKey) {
    open(NFLUENT_WALLET+"/?param="+setParams({addr:key.pubkey,toolbar:false,takePhoto:true,network:this.network.network}))
  }

  open_collections(key: CryptoKey) {
    this.router.navigate(["collections"],{queryParams:{owner:key.pubkey}});
  }
}
