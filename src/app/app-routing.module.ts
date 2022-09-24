import {NgModule} from '@angular/core';
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
import {AdminComponent} from "./admin/admin.component";
import {FaqsComponent} from "./faqs/faqs.component";
import {DispenserComponent} from "./dispenser/dispenser.component";
import {StoreComponent} from "./store/store.component";

import {CandymachineComponent} from "./candymachine/candymachine.component";
import {PageNotFoundComponent} from "./page-not-found/page-not-found.component";
import {IntroComponent} from "./intro/intro.component";
import {LoginComponent} from "./login/login.component";


const routes: Routes = [
  { path: 'wallet', component: MywalletComponent },
  { path: 'candymachine', component:CandymachineComponent },
  { path: 'cm', component:CandymachineComponent,pathMatch:"prefix" },
  { path: 'dealermachine', component:DealermachineComponent ,pathMatch:"prefix"},
  { path: 'dm', component:DealermachineComponent },

  { path: 'help', component: HelpComponent },
  { path: 'about', component: AboutComponent },
  { path: 'reload', component: FaucetComponent },
  { path: 'faqs', component: FaqsComponent },
  { path: 'login', component: LoginComponent },
  { path: 'mint', component: MintComponent },
  { path: 'miner', component: MintComponent },
  { path: 'keys', component: KeysComponent },
  { path: 'admin', component: AdminComponent },
  { path: 'contest', component: ContestComponent },
  { path: 'dispenser', component: DispenserComponent,pathMatch:"prefix" },
  { path: 'creator', component: CreatorComponent },
  { path: 'store', component: StoreComponent },
  { path: 'manage', component: ManageComponent },
  { path: 'build', component:BuildOpeComponent },
  { path: 'validate', component: ValidateComponent },
  { path: 'buy', component: BuyComponent },
  { path: 'pagenotfound', component: PageNotFoundComponent},
  { path: 'intro', component: IntroComponent },
  { path: '', component: IntroComponent,pathMatch: 'full' },
  { path: '**', component: PageNotFoundComponent },
];

@NgModule({
  imports: [RouterModule.forRoot(routes)],
  exports: [RouterModule]
})

export class AppRoutingModule { }
