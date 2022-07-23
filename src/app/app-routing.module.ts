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
import {LoginComponent} from "./login/login.component";


const routes: Routes = [
  { path: 'help', component: HelpComponent },
  { path: 'about', component: AboutComponent },
  { path: 'reload', component: FaucetComponent },
  { path: 'faqs', component: FaqsComponent },
  { path: 'mint', component: MintComponent },
  { path: 'keys', component: KeysComponent },
  { path: 'admin', component: AdminComponent },
  { path: 'contest', component: ContestComponent },
  { path: 'dispenser', component: DispenserComponent },
  { path: 'creator', component: CreatorComponent },
  { path: 'store', component: StoreComponent },
  { path: 'login', component: LoginComponent },
  { path: 'manage', component: ManageComponent },
  { path: 'dealermachine', component:DealermachineComponent },
  { path: 'dm', component:DealermachineComponent },
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
