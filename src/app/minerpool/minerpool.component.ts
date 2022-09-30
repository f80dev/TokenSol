import { Component, OnInit } from '@angular/core';
import {NFT} from "../../nft";
import {NetworkService} from "../network.service";
import {resolveAny} from "dns";
import {showMessage} from "../../tools";

interface Ask {
  id:string
  nft:NFT
  dtWork: Number
  tx: string
  operation:string
  miner:string
}

@Component({
  selector: 'app-minerpool',
  templateUrl: './minerpool.component.html',
  styleUrls: ['./minerpool.component.css']
})
export class MinerpoolComponent implements OnInit {
  asks: Ask[]=[];
  message: string="";

  constructor(
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    this.network.get_minerpool().subscribe((r:any)=>{
      this.asks=r;
    })
  }

  run() {
    this.message="Traitement en cours";
    this.network.run_mintpool(10).subscribe(()=>{
      this.message="";
      this.refresh();
    });
  }

  cancel(ask: Ask) {
    this.network.cancel_mintpool_treatment(ask.id).subscribe(()=>{
      this.refresh();
    })
  }
}
