import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {MetabossService} from "../metaboss.service";
import {ActivatedRoute} from "@angular/router";
import {Location} from "@angular/common"
import {$$, showError, showMessage} from "../../tools";
import {FilterPipe} from "../filter.pipe";
import {Token} from "../nfts/nfts.component";
import {AliasPipe} from "../alias.pipe";
import {MatSelectChange} from "@angular/material/select";
import {MatSnackBar} from "@angular/material/snack-bar";
import {ClipboardModule} from "@angular/cdk/clipboard";
import {stringify} from "querystring";


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
  type_addr="owner";
  addrs: string[]=[];

  constructor(
    public network:NetworkService,
    public metaboss:MetabossService,
    public clipboard:ClipboardModule,
    public routes:ActivatedRoute,
    public _location:Location,
    public toast:MatSnackBar,
    private filterPipe:FilterPipe,
    private alias_pipe:AliasPipe
  ) {}


  ngOnInit(): void {
    this.refresh();
    let account=this.routes.snapshot.queryParamMap.get("account") || "";
    this.type_addr=this.routes.snapshot.queryParamMap.get("search") || "owner";
    this.pubkey=this.routes.snapshot.queryParamMap.get("view") || "";
    setTimeout(()=>{
      this.metaboss.sel_key(account).then(()=>{
        this.refresh();
      });
    },500);
  }


  clear_pubkey(){
    this.pubkey="";
    this.refresh();
  }


  refresh() {
    if(this.type_addr=="token_list"){
      this.nfts=[];
      for(let a of this.addrs){
        this.network.get_tokens_from("token",a,this.limit).then((r:any)=> {
          this.nfts.push(r[0]);
        });
      }
    }else{
      if(this.metaboss.admin_key && this.type_addr!=""){
        let new_url="./manage/?search="+this.type_addr+"&account="+this.metaboss.admin_key.name+"&view="+this.pubkey+"&network="+this.network.network;
        this._location.replaceState(new_url);
        this.nfts=[];
        let pubkey=this.alias_pipe.transform(this.pubkey,"pubkey");

        if(this.type_addr=="token" && pubkey.length<40)return;
        if(pubkey.length==0)return;

        this.network.wait("Récupération des NFT par "+this.type_addr+" pour "+pubkey);
        this.network.get_tokens_from(this.type_addr, pubkey,this.limit).then((r:any)=>{
          showMessage(this,r.length+" NFTs affichés");
          this.network.wait("")
          this.nfts=r;
        }).catch(err=>{this.network.wait("");showError(this,err);});
      }
    }
  }



  burn_all() {
    let nfts:Token[]=this.filterPipe.transform(this.nfts,['search_collection',this.search_collection]);
    nfts=this.filterPipe.transform(nfts,['search_metadata',this.search_metadata]);
    let i=0;
    for(let nft of nfts){
      i=i+1;
      setTimeout(()=>{
        $$("Destruction de "+nft.address)
        this.metaboss.burn(nft.address,this.network.network,5).then(success=>{
          if(i==nfts.length){
            showMessage(this,"détruit");
            this.refresh();
          }
        }).catch(err => {showError(this,err)})
      },i*5000)

    }

  }

  onkeypress($event: KeyboardEvent) {
    if($event.keyCode==13){
      localStorage.setItem("view",this.pubkey);
      this.refresh();
    }
  }

  change_typeaddr($event: MatSelectChange) {
    this.refresh();
  }

  // uploaded(file:any) {
  //   this.network.get_list_tokens().subscribe((r:any)=>{
  //     this.addrs=r;
  //     this.refresh();
  //   });
  // }

  limit=20;
  paste_list(evt:ClipboardEvent) {
    if(evt.clipboardData){
      this.addrs=evt.clipboardData.getData("text").split("\r\n");
      this.refresh();
    }
  }
}
