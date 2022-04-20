import {Component, NgModule} from '@angular/core';
import {RouterModule, Routes} from "@angular/router";

import {HelpComponent} from "./help/help.component";
import {AboutComponent} from "./about/about.component";
import {BuyComponent} from "./buy/buy.component";
import {FaucetComponent} from "./faucet/faucet.component";
import {MywalletComponent} from "./mywallet/mywallet.component";
import {KeysComponent} from "./keys/keys.component";
import {MintComponent} from "./mint/mint.component";
import {ManageComponent} from "./manage/manage.component";


const routes: Routes = [
  { path: 'help', component: HelpComponent },
  { path: 'about', component: AboutComponent },
  { path: 'reload', component: FaucetComponent },
  { path: 'mint', component: MintComponent },
  { path: 'keys', component: KeysComponent },
  { path: 'manage', component: ManageComponent },
  { path: 'wallet', component: MywalletComponent },
  { path: 'buy', component: BuyComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})

export class AppRoutingModule { }
