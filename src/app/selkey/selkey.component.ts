import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";

@Component({
  selector: 'app-selkey',
  templateUrl: './selkey.component.html',
  styleUrls: ['./selkey.component.css']
})
export class SelkeyComponent implements OnInit,OnChanges {

  @Input("network") network:string="";
  @Output("addrChange") onAddrChange:EventEmitter<string>=new EventEmitter();

  sel_addr: any;
  constructor(public network_service:NetworkService,public user:UserService) { }

  ngOnInit(): void {
  }

  onChangeKey($event: any) {
    this.sel_addr=$event;
    this.onAddrChange.emit($event);
  }

  ngOnChanges(changes: SimpleChanges): void {

  }
}
