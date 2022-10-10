import { Component, OnInit } from '@angular/core';
import {getParams, setParams, showError, showMessage} from "../../tools";
import {Collection, Operation} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Body} from "node-fetch";

@Component({
  selector: 'app-candymachine',
  templateUrl: './candymachine.component.html',
  styleUrls: ['./candymachine.component.css']
})
export class CandymachineComponent implements OnInit {
  operation: Operation | null=null;
  showEnd: boolean=false;
  collections: Collection[]=[];


  constructor(
    public routes:ActivatedRoute,
    public router:Router,
    public toast:MatSnackBar,
    public _location:Location,
    public network: NetworkService
  ) { }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.network.get_operations(params["ope"]).subscribe((operation:any)=>{
        this.operation=operation;
        for(let col of operation.collections){
          if(operation.candymachine.collections.indexOf(col.id)>-1){
            this.collections.push(col);
          }
        }
      },(err:any)=>{
        showError(this,err);
      })
    }).catch(()=>{
      debugger
    })
  }


  authent($event: any) {
    if(this.operation?.network){
      let body={
        owner:$event.address,
        network:this.operation?.network,
        miner: this.operation.lazy_mining.miner,
        operation:this.operation.id,
        collection:this.operation.candymachine.collections[0]
      }
      this.network.add_user_for_nft(body).subscribe(()=>{
        this.showEnd=true;
      })
    }
  }

  back() {
    this._location.back();
  }


}
