import {
  Component,
  EventEmitter,
  Input,
  OnChanges, OnInit,
  Output,
  SimpleChanges
} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {MatDialog} from "@angular/material/dialog";
import {CryptoKey,  newCryptoKey, setParams} from "../../tools";
import {_prompt} from "../prompt/prompt.component";
import {Router} from "@angular/router";
import {wait_message} from "../hourglass/hourglass.component";

@Component({
  selector: 'app-selkey',
  templateUrl: './selkey.component.html',
  styleUrls: ['./selkey.component.css']
})
export class SelkeyComponent implements OnChanges {

  @Input("network") network:string="";
  @Input("filter") filter:string="";
  @Input() label:string="Clés disponibles";
  @Input("key") sel_key:CryptoKey | undefined;
  @Input() default_index=0;
  @Input() with_balance=true;
  @Input("can_use_own_key") can_use_own_key=false;
  @Input("can_see_nfluent_wallet") can_see_nfluent_wallet=true;
  @Input("can_see_explorer") can_see_explorer=true;
  @Output("onChange") onAddrChange:EventEmitter<CryptoKey>=new EventEmitter();
  keys: CryptoKey[]=[];
  message=""


  constructor(public network_service:NetworkService,
              public dialog:MatDialog,
              public router:Router,
              public user:UserService) {
  }


  ngOnChanges(changes: SimpleChanges): void {
    if(changes){
      this.keys=[]
      wait_message(this,"Chargement ...")
      this.network_service.init_keys(this.with_balance,"","",this.network).then((keys:CryptoKey[])=>{
        wait_message(this)
        for(let k of keys){
          if(k && k.name){
            if(this.filter=="" || this.filter.split(",").indexOf(k.name)>-1){
              this.keys.push(k)
            }
          }
        }
        if(this.keys.length>0 && this.default_index>-1 && this.default_index<this.keys.length){
          this.sel_key=this.keys[this.default_index]
          this.onAddrChange.emit(this.sel_key);
        }
      })
    }
  }




  isFree(){
    return this.network.indexOf("devnet")>-1 || this.network.startsWith("db-") || this.network.startsWith("file-");
  }


  onChangeKey(new_key:any) {
    if(new_key){
      this.onAddrChange.emit(new_key);
    }
  }


  async paste_key() {
    let privatekey=await _prompt(this,"Utiliser votre clé","","Cette clé reste confidentiel","text","Utiliser","Annuler",false);
    this.network_service.encrypte_key("mykey",this.network,privatekey).subscribe((r:any)=>{
      let k=newCryptoKey(r.address,"mykey",privatekey)
      this.network_service.keys.push(k)
      this.sel_key=k;
      this.onChangeKey(k);
    })
  }

  open_wallet() {
    let url="https://wallet.nfluent.io/?"+setParams({addr: this.sel_key?.address,network: this.network_service.network}, "")
    open(url,"wallet")
  }

  open_explorer() {
    if(this.sel_key) this.network_service.open_explorer(this.sel_key.address,"address")
  }
}
