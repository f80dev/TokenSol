import {
  AfterContentInit,
  AfterViewInit,
  Component,
  EventEmitter,
  Input,
  OnChanges,
  OnInit,
  Output,
  SimpleChanges
} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {MatDialog} from "@angular/material/dialog";
import {CryptoKey, encrypt, newCryptoKey, setParams} from "../../tools";
import {_prompt} from "../prompt/prompt.component";
import {Router} from "@angular/router";

@Component({
  selector: 'app-selkey',
  templateUrl: './selkey.component.html',
  styleUrls: ['./selkey.component.css']
})
export class SelkeyComponent implements AfterViewInit {

  @Input("network") network:string="";
  @Input() label:string="Clés disponibles";
  @Output("onChange") onAddrChange:EventEmitter<CryptoKey>=new EventEmitter();

  sel_key: CryptoKey | undefined;
  constructor(public network_service:NetworkService,
              public dialog:MatDialog,
              public router:Router,
              public user:UserService) {
  }



  ngAfterViewInit(): void {
    setTimeout(()=>{
      if(localStorage.getItem("key")){
        for(let k of this.network_service.keys){
          if(k.address==localStorage.getItem("key"))
            this.sel_key=k;
        }
      }
    },500)
    }


  onChangeKey(k: CryptoKey) {
    this.sel_key=k;
    localStorage.setItem("key",this.sel_key.address);
    this.onAddrChange.emit(k);
  }


  async paste_key() {
    let privatekey=await _prompt(this,"Utiliser votre clé","","Cette clé reste confidentiel","text","Utiliser","Annuler",false);
    this.network_service.encrypte_key("mykey",this.network,privatekey).subscribe((r:any)=>{
      let k=newCryptoKey(r.address,"mykey",privatekey)
      this.network_service.keys.push(k)
      this.onChangeKey(k);
    })
  }

  open_wallet() {
    this.router.navigate(["mywallet"], {
          queryParams: {p:setParams({
              addr: this.sel_key?.address,
              network: this.network_service.network
            }, "", "")}
        }
    );
  }
}