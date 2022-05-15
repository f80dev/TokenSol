import { Component, OnInit } from '@angular/core';
import {ActivatedRoute} from "@angular/router";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";

  constructor(
    public routes:ActivatedRoute,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
  }

  valide(evt: any) {
    if(this.address.indexOf("@")>4){
      this.network.send_confirmation(this.address).subscribe(()=>{});
    }
  }
}
