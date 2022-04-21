import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {NetworkService} from "../network.service";
import {removeBigInt, showError} from "../../tools";

@Component({
  selector: 'app-mywallet',
  templateUrl: './mywallet.component.html',
  styleUrls: ['./mywallet.component.css']
})
export class MywalletComponent implements OnInit {
  nfts: any;
  indexTab: number=0;

  constructor(public user:UserService,public network:NetworkService) { }

  ngOnInit(): void {
    this.user.connect(()=>{
      this.refresh();
    });
  }

  refresh(index:number=0) {
    this.network.wait("Chargement de vos NFTs");
    this.network.get_tokens_from_owner(this.user.wallet.publicKey!.toBase58(),"by_owner").then((r:any[])=>{
      this.network.wait("");
      this.nfts=[];
      for(let t of r){
        if(index==0){
          this.nfts.push({
            offchain:t.offchain,
            mint:t.accountInfo.mint,
            owner:t.accountInfo.owner,
            updateAuthority:t.solscan.metadata.updateAuthority,
            mintAuthority:t.layoutInfo.mintAuthority,
            freezeAuthority:t.layoutInfo.freezeAuthority
          });
        } else {
          this.nfts.push(removeBigInt(t));
        }
      }
    }).catch(err=>{showError(this,err)});
  }
}
