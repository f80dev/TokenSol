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
export class SelkeyComponent implements AfterViewInit,OnChanges {

  @Input("network") network:string="";
  @Input() label:string="Clés disponibles";
  @Input("key") sel_key:CryptoKey | undefined;
  @Output("onChange") onAddrChange:EventEmitter<CryptoKey>=new EventEmitter();


  constructor(public network_service:NetworkService,
              public dialog:MatDialog,
              public router:Router,
              public user:UserService) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    if(changes["sel_key"] && changes["sel_key"].previousValue!=changes["sel_key"].currentValue){
        let k=this.network_service.find_key_by_address(changes["sel_key"].currentValue.address)
        if(k)this.sel_key=this.network_service.keys[this.network_service.keys.indexOf(k)];
    }
  }




  isFree(){
    return this.network.indexOf("devnet")>-1 || this.network.startsWith("db-") || this.network.startsWith("file-");
  }

  ngAfterViewInit(): void {
      // for(let k of this.network_service.keys){
      //   if(k.address==localStorage.getItem("key"))
      //     this.sel_key=k;
      // }
    }


  onChangeKey(new_key:any) {
    if(new_key){
      localStorage.setItem("key",new_key.address);
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
    this.router.navigate(["mywallet"], {
          queryParams: {p:setParams({
              addr: this.sel_key?.address,
              network: this.network_service.network
            }, "", "")}
        }
    );
  }
}
