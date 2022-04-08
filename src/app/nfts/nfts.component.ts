import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {PublicKey} from "@solana/web3.js";
import {$$, toStringify} from "../../tools";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {NftstorageService} from "../nftstorage.service";
import {MetabossService} from "../metaboss.service";


@Component({
  selector: 'app-nfts',
  templateUrl: './nfts.component.html',
  styleUrls: ['./nfts.component.css']
})
export class NftsComponent implements OnChanges {

  @Input("nfts") nfts: any;
  @Input("format") format: string="str";
  @Output('refresh') onrefresh: EventEmitter<any>=new EventEmitter();
  nfts_out: any[] =[];

  constructor(
    public user:UserService,
    public network:NetworkService,
    public nftstorage:NftstorageService,
    public dialog:MatDialog,
    public metaboss:MetabossService
  ) {}



  toString(tokenInfo:any,sep="\n"){
    let s=toStringify(tokenInfo)
    for(let i=0;i<20;i++){
      s=s.replace("\",\"","\""+sep+"\"")
      s=s.replace("{\"","{"+sep+"\"").replace("\"}","\""+sep+"}")
    }

    if(this.format=="html"){
      for(let v of Object.values(tokenInfo)){
        // @ts-ignore

        if(v?.constructor.name=="PublicKey"){
          // @ts-ignore
          let addr=v.toBase58().trim();
          s=s.replace(addr,"<a target=_blank href='https://solscan.io/account/"+addr+"?cluster="+this.network.network+"'>"+addr+"</a>");
        }

      }
    }

    return s;
  }


  ngOnChanges(changes: SimpleChanges): void {
    if(this.nfts){
      let sep="\n";
      this.nfts_out=this.nfts;
      if(this.format=="str")sep="\n";
      if(this.format=="html")sep="<br>";
      if(this.format=="html" || this.format=="str")this.nfts_out=this.nfts.map((x:any) => this.toString(x,sep))
    }
  }


  ask_for_attribute(default_value:any,title:string) {
    return new Promise((resolve, reject) => {
      this.dialog.open(PromptComponent,{
        width: 'auto',data:
          {
            title: "Modification de "+title,
            type: "text",
            value:default_value,
            placeholder:default_value,
            onlyConfirm:false,
            lbl_ok: "Ok",
            lbl_cancel: "Annuler"
          }
      }).afterClosed().subscribe(resp => {
        if(resp)
          resolve(resp);
        else
          reject(resp);
      });
    });
  }

  update(nft: any) {

  }


  burn(nft:any) {
    this.metaboss.burn(nft.mint).then(success=>{
      if(success)this.onrefresh.emit();
    })
  }

  update_field(attr: any, nft: any) {
    this.ask_for_attribute(attr.value,attr.trait_type).then(new_value=>{
      for(let i=0;i<nft.offchain.attributes.length;i++){
        if(nft.offchain.attributes[i]==attr){
          nft.offchain.attributes[i].value=new_value;
          break;
        }
      }
      $$("Demande de stockage pour ",nft.offchain);
      this.nftstorage.store(nft.offchain).then(url=>{
        $$("NFT storage retourne l'url "+url);
        this.metaboss.update(nft.mint,url).then(success=>{
          $$("Mise a jour")
          debugger
        })
      })
    })
  }
}
