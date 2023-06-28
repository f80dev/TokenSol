import {Injectable, OnInit} from '@angular/core';

//voir https://github.com/patrickniyo/ng-connect-eth-wallet/blob/master/src/app/app.component.ts

@Injectable({
  providedIn: 'root'
})
export class EvmWalletServiceService {
  public ethereum;
  constructor() {
    const {ethereum} = <any>window
    this.ethereum = ethereum
  }



  async connectWallet() {
    try{
      if(!this.ethereum) return alert("Please install meta mask");
      const accounts = await this.ethereum.request({method: 'eth_requestAccounts'});
    }
    catch(e){
      throw new Error("No thereum object found")
    }
  }



  async checkWalletConnected () {
    try{
      if(!this.ethereum) return alert("Please install meta mask ")
      const accounts = await this.ethereum.request({method: 'eth_accounts'});
      return accounts;
    }
    catch(e){
      throw new Error("No ethereum object found");
    }
  }
}
