import {AccountLayout, TOKEN_PROGRAM_ID} from "@solana/spl-token";
import {Component, Input, OnInit} from '@angular/core';
import {UserService} from "../user.service";
import {AccountInfo, PublicKey, RpcResponseAndContext} from "@solana/web3.js";

@Component({
  selector: 'app-buy',
  templateUrl: './buy.component.html',
  styleUrls: ['./buy.component.css']
})
export class BuyComponent implements OnInit {



  private tokens: any;

  constructor(
    private user:UserService
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    //voir https://solana-labs.github.io/solana-web3.js/classes/Connection.html#getTokenAccountsByOwner

  }

}
