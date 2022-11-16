import {Component, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {UserService} from "../user.service";
import {OperationService} from "../operation.service";
import {NFT} from "../../nft";
import {environment} from "../../environments/environment";
import {getParams} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {Operation} from "../../operation";

@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css']
})
export class AnalyticsComponent implements OnInit {
  nfts: NFT[] = [];
  transactions: any[]=[]
  graph: any;

  constructor(
    public network:NetworkService,
    public user:UserService,
    public routes:ActivatedRoute,
    public operation:OperationService
  ) { }

  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("collection"))
        this.from_collection(params.collection);
      else{
        if(this.operation.sel_ope)this.from_operation(this.operation.sel_ope.id);
        this.operation.sel_ope_change.subscribe((new_sel:Operation)=>{
          this.from_operation(new_sel.id);
        })
        this.open_graph();
      }
    })
  }



  from_operation(operation_id:string) {
      this.network.get_nfts_from_operation(operation_id).subscribe((r:any)=>{
        this.nfts=r.nfts;
        setTimeout(()=>{
          for(let i=0;i<this.nfts.length;i++){
            let nft=this.nfts[i];
            if(nft.address)
              this.network.get_nft(nft.address,this.network.network).subscribe((complete_nft:NFT[])=>{
                this.nfts[i]=complete_nft[0];
              })
          }
        })
      });
  }

  open_explorer(nft: NFT) {
    open("https://"+(this.network.isMain() ? "" : "devnet-")+"explorer.elrond.com/nfts/"+nft.address);
  }

  open_graph() {
    this.network.wait("Construction du graph");
    this.network._get(environment.server+"/api/analyse_transaction/"+this.user.addr+"/","limit=50&profondeur_max=5&network="+this.network.network+"&size=50").subscribe((result:any)=>{
      if(result.hasOwnProperty("graph")){
        this.graph=result.graph;
      } else {
        this.transactions=result.transactions;
        this.add_date();
      }
    })
  }

  add_date(){
    for(let transaction of this.transactions)
      transaction.ts_date=new Date(transaction.ts*1000).toLocaleString()
    return true;
  }

  from_collection(collection_id:string) {
    this.nfts=[];
    this.network._get(environment.server+"/api/analyse_transaction/"+collection_id+"/","network="+this.network.network+"&format=transactions&size=500").subscribe((result:any)=>{
      this.transactions=result.transactions;
      this.add_date();
    })
  }

  open_transaction(transaction: any) {
    open("https://"+(this.network.isMain() ? "" : "devnet-")+"explorer.elrond.com/transactions/"+transaction.id);
  }
}
