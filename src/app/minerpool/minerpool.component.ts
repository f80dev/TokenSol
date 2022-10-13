import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {Source} from "../../operation";

interface Ask {
  id:string
  dtCreate: number
  dtStart: number
  dtWork: number
  dest:string
  message: string
  filter:string[]
  network:string
  miner:string
  sources:Source[]
}

@Component({
  selector: 'app-minerpool',
  templateUrl: './minerpool.component.html',
  styleUrls: ['./minerpool.component.css']
})
export class MinerpoolComponent implements OnInit {
  asks: Ask[]=[];
  message: string="";
  showAll: boolean=false;

  constructor(
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    this.network.get_minerpool().subscribe((r:any)=>{
      if(!this.showAll && r.length<10)this.showAll=true;
      this.asks=[];
      for(let ask of r){
        ask.sources=ask.sources.filter((x:Source) => x.active)
        if(this.showAll || ask.dtWord )this.asks.push(ask);
      }
    })
  }

  run(filter="") {
    this.message="Traitement en cours";
    this.network.run_mintpool(10,filter).subscribe(()=>{
      this.message="";
      this.refresh();
    });
  }

  cancel(ask: Ask) {
    this.network.cancel_mintpool_treatment(ask.id).subscribe(()=>{
      this.refresh();
    })
  }

  reset_pool() {

  }

  ConvertDate(dt: number) {
    return new Date().setTime(dt);
  }

  retry(ask: Ask) {
    this.network.edit_mintpool(ask.id,{dtWork:"",message:"to_mint"}).subscribe(()=>{this.refresh()});
  }
}
