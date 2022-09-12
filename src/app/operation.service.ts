import {Injectable} from '@angular/core';
import {NetworkService} from "./network.service";
import {Operation} from "../operation";
import {ActivatedRoute} from "@angular/router";

@Injectable({
  providedIn: 'root'
})
export class OperationService {

  opes:Operation[]=[];
  sel_ope:Operation | null=null;

  constructor(
    public network: NetworkService,
    public routes:ActivatedRoute,
  ) {
    this.refresh();
  }

  select(operation_id:string) {
    for(let sel of this.opes){
      if(sel.id==operation_id)this.sel_ope=sel;
    }
  }

  refresh(){
    if(this.opes.length==0){
      this.network.get_operations().subscribe((r:any)=>{
        this.opes=r;
        if(!this.sel_ope && this.opes.length>0){
          this.sel_ope=r[r.length-1];
        }
      })
    }
  }



}

