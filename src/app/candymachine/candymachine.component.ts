import { Component, OnInit } from '@angular/core';
import {getParams, setParams, showError, showMessage} from "../../tools";
import {Collection, Operation} from "../../operation";
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {Location} from "@angular/common";

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
    public _location:Location,
    public network: NetworkService
  ) { }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      this.network.get_operations(params["ope"]).subscribe((operation:any)=>{
        this.operation=operation;
        for(let col of operation.collections){
          if(operation.candymachine.collections.indexOf(col.name)>-1){
            this.collections.push(col);
          }
        }
      },(err:any)=>{
        debugger
        showError(this,err);
      })
    }).catch(()=>{
      debugger
    })
  }

  // random_nft(ope_id:string,limit:number=100)  {
  //   this.network.get_tokens_to_send(ope_id,"candymachine",limit).subscribe((nfts:any) => {
  //     if(nfts.length>0){
  //       let idx=Math.random()*nfts.length;
  //
  //       this.router.navigate(["dealermachine"],{queryParams:{param:setParams({
  //             token:nfts[idx],
  //             price:0,
  //             ope: this.operation!.id,
  //             selfWalletConnexion:true,
  //             mining:this.operation!.lazy_mining
  //           })}})
  //     }
  //   });
  // }


  authent($event: any) {
    this.network.add_user_for_nft($event,this.network.network,this.operation!.id,this.operation?.candymachine.collections).subscribe(()=>{
      this.showEnd=true;
    })
  }

  back() {
    this._location.back();
  }
}
