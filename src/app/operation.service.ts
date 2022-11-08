import {Injectable} from '@angular/core';
import {NetworkService} from "./network.service";
import {Operation} from "../operation";
import {Subject} from "rxjs";

@Injectable({
  providedIn: 'root'
})
export class OperationService {

  opes:Operation[]=[];
  sel_ope:Operation | null=null;
  sel_ope_change=new Subject<Operation>();

  constructor(
    public network: NetworkService,
  ) {
    this.refresh();
  }

  get_operation_from_web(url:string){
    this.network.get_operations(url).subscribe((ope:Operation)=>{
      this.opes.push(ope);
      this.sel_ope=this.opes[this.opes.length-1]
    })
  }

  select(operation_id:string) {
    if(operation_id && operation_id.startsWith("b64:")){
      this.get_operation_from_web(operation_id);
    }else{
      for(let sel of this.opes){
        if(sel.id==operation_id){
          this.sel_ope=sel;
          this.sel_ope_change.next(sel);
        }
      }
    }

  }

  refresh(){
    if(this.opes.length==0){
      this.network.get_operations().subscribe((r:any)=>{
        this.opes=r;
        if(!this.sel_ope && this.opes.length>0){
          this.sel_ope=r[r.length-1];
          if(this.sel_ope)this.sel_ope_change.next(this.sel_ope);
        }
      })
    }
  }



}

