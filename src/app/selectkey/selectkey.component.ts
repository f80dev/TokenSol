import {Component, EventEmitter, Input, OnInit, Output} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {MatSelectChange} from "@angular/material/select";
import {MetabossKey, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";

@Component({
  selector: 'app-selectkey',
  templateUrl: './selectkey.component.html',
  styleUrls: ['./selectkey.component.css']
})
export class SelectkeyComponent implements OnInit {
  keys: MetabossKey[]=[];
  selected:MetabossKey | undefined;
  @Input("fontsize") fontsize="x-small";
  @Output('refresh') onrefresh: EventEmitter<any>=new EventEmitter();

  constructor(private metaboss:MetabossService,public toast:MatSnackBar) { }

  ngOnInit(): void {
    this.metaboss.keys().subscribe((keys)=>{
      this.keys=keys;
      let fix_key=localStorage.getItem("key") || "paul";
      for(let k of keys){
        if(k.name==fix_key){
          this.metaboss.admin_key=k;
          this.selected=k;
        }
      }
    })
  }

  refresh($event: MatSelectChange) {
    this.metaboss.admin_key=$event.value;
    localStorage.setItem("key",this.metaboss.admin_key?.name!);
    this.onrefresh.emit($event);
  }

  informe_copy() {
    showMessage(this,"Adresse de "+this.selected?.name+" copiée");
  }

  refill() {
    this.metaboss.airdrop(2);
  }
}
