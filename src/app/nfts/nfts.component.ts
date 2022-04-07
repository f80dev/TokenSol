import {Component, Input, OnChanges, OnInit, SimpleChanges} from '@angular/core';
import * as SPLToken from "@solana/spl-token";
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {PublicKey} from "@solana/web3.js";

@Component({
  selector: 'app-nfts',
  templateUrl: './nfts.component.html',
  styleUrls: ['./nfts.component.css']
})
export class NftsComponent implements OnChanges {

  @Input("pubkey") pubkey: PublicKey | undefined;
  nfts: any[] =[];


  constructor(
    public user:UserService,
    public network:NetworkService
  ) { }

  ngOnInit(): void {

  }

  toStringify(obj:any) {
    return JSON.stringify(obj, (key, value) =>
      typeof value === 'bigint'
        ? value.toString()
        : value // return everything else unchanged
    );
  }

  ngOnChanges(changes: SimpleChanges): void {
    if(this.pubkey){
      this.network.get_tokens(this.pubkey!).then((r:any)=>{
        this.nfts=[];
        for(let e of r){
          const accountInfo:any= SPLToken.AccountLayout.decode(e.account.data);
          const layoutInfo=SPLToken.MintLayout.decode(e.account.data);
          let tokenInfo={...accountInfo, ...layoutInfo}
          tokenInfo["pubkey"]=e.pubkey;
          let s=this.toStringify(tokenInfo)
          for(let i=0;i<50;i++)
            s=s.replace("\",\"","\"\n,\"")

          this.nfts.push(s);
        }
      })
    }
  }

}
