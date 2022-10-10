import { Component, OnInit } from '@angular/core';
import {clusterApiUrl, Connection, LAMPORTS_PER_SOL, PublicKey, TransactionSignature} from '@solana/web3.js';
import {UserService} from "../user.service";
import {Observable, Observer} from "rxjs";
import {NetworkService} from "../network.service";
import {ActivatedRoute} from "@angular/router";

// @ts-ignore
// @ts-ignore
@Component({
  selector: 'app-faucet',
  templateUrl: './faucet.component.html',
  styleUrls: ['./faucet.component.css']
})
export class FaucetComponent implements OnInit {

  public balance: Promise<number> | undefined;

  constructor(public user:UserService,
              public routes:ActivatedRoute,
              public network:NetworkService) { }

  ngOnInit(): void {
    if(this.network.isSolana())
      this.user.login();
  }

  refresh(){
    // this.balance=this.network.getBalance(<PublicKey>this.user.wallet.publicKey);
  }

  reload() {
    if(this.network.isElrond())
      open("https://r3d4.fr/elrond/devnet/index.php","_blank")
    else{
      // this.network.airdrop(this.user.wallet.publicKey!).then(()=>{
      //   this.refresh();
      // });
    }

  }



}
