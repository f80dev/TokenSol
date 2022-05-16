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
import {CreatorComponent} from "./creator/creator.component";
import {ValidateComponent} from "./validate/validate.component";
import {DealermachineComponent} from "./dealermachine/dealermachine.component";
import {ContestComponent} from "./contest/contest.component";
import {BuildOpeComponent} from "./build-ope/build-ope.component";


const routes: Routes = [
  { path: 'help', component: HelpComponent },
  { path: 'about', component: AboutComponent },
  { path: 'reload', component: FaucetComponent },
  { path: 'mint', component: MintComponent },
  { path: 'keys', component: KeysComponent },
  { path: 'contest', component: ContestComponent },
  { path: 'creator', component: CreatorComponent },
  { path: 'manage', component: ManageComponent },
  { path: 'dealermachine', component:DealermachineComponent },
  { path: 'build', component:BuildOpeComponent },
  { path: 'validate', component: ValidateComponent },
  { path: 'wallet', component: MywalletComponent },
  { path: 'buy', component: BuyComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})

export class AppRoutingModule { }
