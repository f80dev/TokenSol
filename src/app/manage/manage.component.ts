import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {MetabossService} from "../metaboss.service";
import {ActivatedRoute} from "@angular/router";
import {Location} from "@angular/common"
import {showError, showMessage} from "../../tools";
import {FilterPipe} from "../filter.pipe";

@Component({
  selector: 'app-manage',
  templateUrl: './manage.component.html',
  styleUrls: ['./manage.component.css']
})
export class ManageComponent implements OnInit {
  nfts: any;
  pubkey: string="";
  search_metadata: string = "";
  search_collection:string="";

  constructor(
    public network:NetworkService,
    public metaboss:MetabossService,
    public routes:ActivatedRoute,
    public _location:Location,
    private filterPipe:FilterPipe
  ) {}


  ngOnInit(): void {
    this.refresh();
    let account=this.routes.snapshot.queryParamMap.get("account") || "";
    this.pubkey=this.routes.snapshot.queryParamMap.get("view") || account || localStorage.getItem("view") || "";
    setTimeout(()=>{
      this.metaboss.sel_key(account).then(()=>{
        this.refresh();
      });
    },500);
  }



  refresh() {
    if(this.metaboss.admin_key && (this.pubkey.length>40 || this.network.network.indexOf("elrond")>-1)){
      this.network.wait("Récupération des NFT");
      this._location.replaceState("./manage/?account="+this.metaboss.admin_key.name+"&view="+this.pubkey+"&network="+this.network.network);
      this.nfts=[];
      this.network.get_tokens_from_owner(this.pubkey).then((r:any[])=>{
        this.network.wait("")
        this.nfts=r;
      });

    }
  }



  change_view() {
    if(this.pubkey.length==43){
      localStorage.setItem("view",this.pubkey);
      this.refresh();
    }
  }



  burn_all() {
    let nfts=this.filterPipe.transform(this.nfts,['search_collection',this.search_collection]);
    nfts=this.filterPipe.transform(nfts,['search_metadata',this.search_metadata]);
    for(let nft of nfts){
      this.metaboss.burn(nft.accountInfo.mint,this.network.network).then(success=>{
        showMessage(this,"détruit");
      }).catch(err => {showError(this,err)})
    }

  }
}
