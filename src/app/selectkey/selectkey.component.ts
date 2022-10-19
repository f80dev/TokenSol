import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {MatSelectChange} from "@angular/material/select";
import {CryptoKey, setParams, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";
import {environment} from "../../environments/environment";
import {type} from "os";
import {UserService} from "../user.service";

@Component({
  selector: 'app-selectkey',
  templateUrl: './selectkey.component.html',
  styleUrls: ['./selectkey.component.css']
})
export class SelectkeyComponent implements OnChanges {
  selected: CryptoKey | undefined;
  @Input("fontsize") fontsize = "x-small";
  @Input("selected_addr") selected_addr="";
  @Input() network="elrond-mainnet";
  @Input("keys") keys: CryptoKey[] = [];
  @Output('refresh') onrefresh: EventEmitter<any> = new EventEmitter();

  constructor(private metaboss: MetabossService,
              public user:UserService,
              public toast: MatSnackBar) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    try {
      for(let k of this.keys){
        if(k.pubkey==this.selected_addr){
          this.user.key=k;
          this.selected=k;
        }
      }
    } catch (e) {

    }
  }


  refresh($event: MatSelectChange) {
    this.user.key=$event.value;
    if(this.user.key){
      this.user.init(this.user.key.pubkey).then(()=>{
        localStorage.setItem("key",this.user.key?.name!);
        this.onrefresh.emit($event);
      })
    }
  }

  informe_copy() {
    showMessage(this,"Adresse de "+this.selected?.name+" copiée");
  }

  refill() {
    this.metaboss.airdrop(2);
  }

  open_wallet() {
    let url=environment.wallet+"/wallet/?param="+setParams({addr:this.selected?.pubkey,toolbar:true,network:this.network});
    open(url,"wallet");
  }
}
