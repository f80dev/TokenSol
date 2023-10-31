import { Component, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {MatDialog} from "@angular/material/dialog";
import {StyleManagerService} from "../style-manager.service";
import {$$, apply_params, CryptoKey, getParams, newCryptoKey} from "../../tools";
import { ProxyNetworkProvider } from "@multiversx/sdk-network-providers";
import {ActivatedRoute} from "@angular/router";
import {UserService} from "../user.service";
import {NFT} from "../../nft";
import {newCollection} from "../../operation";
import {WalletConnectV2Provider} from "@multiversx/sdk-wallet-connect-provider/out";
import {
  Transaction,
  TokenTransfer,
  TransactionPayload,
  Address,
  TransferTransactionsFactory, GasEstimator
} from "@multiversx/sdk-core/out";
import {WalletProvider} from "@multiversx/sdk-web-wallet-provider/out";

@Component({
  selector: 'app-tests',
  templateUrl: './tests.component.html',
  styleUrls: ['./tests.component.css']
})
export class TestsComponent implements OnInit {

  owner: string=""
  wallet_provider: any;

  constructor(public api:NetworkService,
              public style:StyleManagerService,
              public toast:MatSnackBar,
              public user:UserService,
              public routes:ActivatedRoute,
              public dialog:MatDialog) {
  }




  async ngOnInit() {
      let params:any=await getParams(this.routes)
      apply_params(this,params)
  }


  authent($event: any) {
    this.wallet_provider=$event.provider
   this.owner=$event.address
  }


}

