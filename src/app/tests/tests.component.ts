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

  num: any;
  nft:NFT={
    address: undefined,
    attributes: [],
    balances: undefined,
    collection: undefined,
    creators: [],
    description: "description",
    files: [],
    links: undefined,
    message: undefined,
    miner: newCryptoKey(),
    name: "montoken",
    network: "elrond-devnet",
    owner: undefined,
    price: undefined,
    royalties: 0,
    solana: undefined,
    style: undefined,
    supply: 1,
    symbol: "montoken",
    tags: "",
    type: "",
    visual: ""
  }
  provider: WalletProvider | undefined;
  miner: CryptoKey | undefined



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


  authent($event: {
    strong: boolean;
    address: string;
    provider: any;
    encrypted: string;
    url_direct_xportal_connect: string
  }) {
    this.nft.miner=newCryptoKey($event.address)
    this.provider=$event.provider;
    this.find_collection($event.address);

  }

  find_collection(addr:string){
    this.api.get_collections(addr,"elrond-devnet").subscribe({
          next:(r:any)=>{
            if(r.length>0){
              this.nft.collection=newCollection(r[0]["name"],this.nft.miner,r[0]["id"],r[0]["type"]);
            }
          }
        }
    )
  }

  async mint() {
    let tmp=await this.api.mint(this.nft)
    await this.api.execute(tmp, "elrond-devnet",this.provider || this.miner)
  }

  setMiner($event:any) {
    this.miner=$event
    this.nft.miner=$event.address
    this.find_collection($event.address)
  }
}

