import { Component, OnInit } from '@angular/core';
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";
import {Location} from "@angular/common"
import {$$, showError, showMessage} from "../../tools";
import {FilterPipe} from "../filter.pipe";

import {AliasPipe} from "../alias.pipe";
import {MatSelectChange} from "@angular/material/select";
import {MatSnackBar} from "@angular/material/snack-bar";
import {NFT} from "../../nft";
import {UserService} from "../user.service";

@Component({
  selector: 'app-manage',
  templateUrl: './manage.component.html',
  styleUrls: ['./manage.component.css']
})
export class ManageComponent implements OnInit {
  nfts: NFT[]=[];
  address: string="";
  search_metadata: string = "";
  search_collection:string="";
  type_addr="owner";
  addrs: string[]=[];

  constructor(
    public network:NetworkService,
    public user:UserService,
    public routes:ActivatedRoute,
    public _location:Location,
    public toast:MatSnackBar,
    public filterPipe:FilterPipe,
    public alias_pipe:AliasPipe
  ) {}



  // test(){
  //   const connection = new Connection("devnet");
  //   const tokenPublicKey = "Gz3vYbpsB2agTsAwedtvtTkQ1CG9vsioqLW3r9ecNpvZ";
  //   Metadata.load(connection, tokenPublicKey).then((r)=>{
  //     console.log(r);
  //   })
  // }

  ngOnInit(): void {
    this.refresh();
    let account=this.routes.snapshot.queryParamMap.get("account") || "";
    this.type_addr=this.routes.snapshot.queryParamMap.get("search") || "owner";
    this.address=this.routes.snapshot.queryParamMap.get("view") || "";
    this.network.network=this.routes.snapshot.queryParamMap.get("network") || "elrond-devnet";
  }


  clear_pubkey(){
    this.address="";
    this.refresh();
  }


  refresh() {
    if(this.type_addr=="token_list"){
      this.nfts=[];
      for(let a of this.addrs){
        this.network.get_tokens_from("token",a,this.limit, false, null, 0,  this.network.network).then((r:any)=> {
          this.nfts.push(r.result[0]);
        });
      }
    }else{
      if(this.user.key && this.type_addr!=""){
        let new_url="./manage/?search="+this.type_addr+"&account="+this.user.key.name+"&view="+this.address+"&network="+this.network.network;
        this._location.replaceState(new_url);
        this.nfts=[];
        let pubkey=this.alias_pipe.transform(this.address,"address");

        if(this.type_addr=="token" && pubkey.length<40)return;
        if(pubkey.length==0)return;

        this.network.wait("Récupération des NFT par "+this.type_addr+" pour "+pubkey);
        this.network.get_tokens_from(this.type_addr, pubkey,this.limit, false, null, 0, this.network.network).then((r:any)=>{
          showMessage(this,r.length+" NFTs affichés");
          this.network.wait("")
          this.nfts=[];
          for(let nft of r){
            if(nft.address && nft.address.length>0)
              this.nfts.push(nft);
          }

          this.nfts.sort((a:NFT, b:NFT) => (a.marketplace!.quantity < b.marketplace!.quantity) ? 1 : -1)
        }).catch(err=>{this.network.wait("");showError(this,err);});
      }
    }
  }


  mass_treatment(func:Function,delay=1){
    let nfts:NFT[]=this.filterPipe.transform(this.nfts,['search_collection',this.search_collection]);
    nfts=this.filterPipe.transform(nfts,['search_metadata',this.search_metadata]);
    let i=0;
    for(let nft of nfts){
      i=i+1;
      setTimeout(()=>{
        $$("Traitement de "+nft.address)
        func(nft);
        if(i==nfts.length){
          showMessage(this,"Opération terminée");
        }
      },delay*i*1000)
    }
  }


  burn_all() {
    this.mass_treatment((nft:NFT)=>{
      this.network.burn(nft.address,this.user.addr,this.network.network,1).then(success=>{}).catch(err => {showError(this,err)})
    })
  }

  transfer_all() {
    this.mass_treatment((nft:NFT)=>{
      if(nft.address && this.user.key){
        this.network.transfer_to(nft.address,this.user.key.address,this.address,this.network.network).subscribe(()=>{
          showMessage(this,nft.address+" transféré");
        })
      }
    },5)
  }

  onkeypress($event: KeyboardEvent) {
    if($event.keyCode==13){
      localStorage.setItem("view",this.address.toLowerCase());
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

  limit=200;
  paste_list(evt:ClipboardEvent) {
    if(evt.clipboardData){
      this.addrs=evt.clipboardData.getData("text").split("\r\n");
      this.refresh();
    }
  }


}
