import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {Source} from "../../operation";
import {_prompt} from "../prompt/prompt.component";
import {environment} from "../../environments/environment";

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
  sources:Source[],
  collection_to_mint:string
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
        if(this.showAll || ask.dtWork )this.asks.push(ask);
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

  reset_pool(all=false) {
    let i=this.asks.length;
    for(let ask of this.asks){
      if(all || (ask.dtWork && ask.dtWork>0)){
        this.network.delete_ask(ask.id).subscribe(()=>{
          i=i-1;
          if((i==0 && all) || (i>0 && !all)){
            this.refresh();
          }
        });
      }
    }
  }

  ConvertDate(dt: number) {
    return new Date().setTime(dt);
  }

  retry(ask: Ask) {
    this.network.edit_mintpool(ask.id,{dtWork:"",message:"to_mint"}).subscribe(()=>{this.refresh()});
  }

  export_pool() {
    open(this.network.server_nfluent+"/api/minerpool?format=csv","export");
  }
}
