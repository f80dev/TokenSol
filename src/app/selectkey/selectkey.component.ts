import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {MatSelectChange} from "@angular/material/select";
import {MetabossKey, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-selectkey',
  templateUrl: './selectkey.component.html',
  styleUrls: ['./selectkey.component.css']
})
export class SelectkeyComponent implements OnInit, OnChanges {
  selected: MetabossKey | undefined;
  @Input("fontsize") fontsize = "x-small";
  @Input("keys") keys: MetabossKey[] = [];
  @Output('refresh') onrefresh: EventEmitter<any> = new EventEmitter();

  constructor(private metaboss: MetabossService,
              public toast: MatSnackBar) {
  }

  ngOnChanges(changes: SimpleChanges): void {
    let fix_key=localStorage.getItem("key") || "paul";
    for(let k of this.keys){
      if(k.name==fix_key){
        this.metaboss.admin_key=k;
        this.selected=k;
      }
    }
    }

  ngOnInit(): void {

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
