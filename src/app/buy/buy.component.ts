import {AccountLayout, TOKEN_PROGRAM_ID} from "@solana/spl-token";
import {Component, Input, OnInit} from '@angular/core';
import {UserService} from "../user.service";
import {AccountInfo, PublicKey, RpcResponseAndContext} from "@solana/web3.js";
import {NetworkService} from "../network.service";

@Component({
  selector: 'app-buy',
  templateUrl: './buy.component.html',
  styleUrls: ['./buy.component.css']
})
export class BuyComponent implements OnInit {
  nfts: any;

  constructor(
    public user:UserService,
    public network:NetworkService
  ) { }

  ngOnInit(): void {
    this.user.connect().then((addr)=>{
      this.network.get_nfts_from_miner(new PublicKey("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")).then(r=>{
        this.nfts=r;
      })
    })
  }

}
