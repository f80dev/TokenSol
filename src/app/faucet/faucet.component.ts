import { Component, OnInit } from '@angular/core';
import {clusterApiUrl, Connection, LAMPORTS_PER_SOL, PublicKey, TransactionSignature} from '@solana/web3.js';
import {UserService} from "../user.service";
import {Observable, Observer} from "rxjs";
import {NetworkService} from "../network.service";

// @ts-ignore
// @ts-ignore
@Component({
  selector: 'app-faucet',
  templateUrl: './faucet.component.html',
  styleUrls: ['./faucet.component.css']
})
export class FaucetComponent implements OnInit {

  public balance: Promise<number> | undefined;

  constructor(public user:UserService,public network:NetworkService) { }

  ngOnInit(): void {
    this.user.connect(()=>{this.refresh();});
  }

  refresh(){
    this.balance=this.network.getBalance(<PublicKey>this.user.wallet.publicKey);
  }

  reload() {
    this.network.airdrop(this.user.wallet.publicKey!);
  }



}
