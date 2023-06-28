import {NgModule} from '@angular/core';
import {RouterModule, Routes} from "@angular/router";

import {HelpComponent} from "./help/help.component";
import {AboutComponent} from "./about/about.component";
import {BuyComponent} from "./buy/buy.component";
import {MywalletComponent} from "./mywallet/mywallet.component";
import {KeysComponent} from "./keys/keys.component";
import {MintComponent} from "./mint/mint.component";
import {ManageComponent} from "./manage/manage.component";
import {MinerpoolComponent} from "./minerpool/minerpool.component";
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
import {CollectionsComponent} from "./collections/collections.component";
import {AutovalidateComponent} from "./autovalidate/autovalidate.component";
import {ValidatorsComponent} from "./validators/validators.component";
import {AnalyticsComponent} from "./analytics/analytics.component";
import {RescuewalletComponent} from "./rescuewallet/rescuewallet.component";
import {SettingsComponent} from "./settings/settings.component";
import {BankComponent} from "./bank/bank.component";
import {RaffleComponent} from "./raffle/raffle.component";
import {TestsComponent} from "./tests/tests.component";

const routes: Routes = [
  { path: 'tests', component: TestsComponent },
  { path: 'test', component: TestsComponent },
  { path: 'wallet', component: MywalletComponent },
  { path: 'autovalidate', component: AutovalidateComponent },
  { path: 'mywallet', component: MywalletComponent },
  { path: 'candymachine', component:CandymachineComponent },
  { path: 'cm', component:CandymachineComponent,pathMatch:"prefix" },
  { path: 'dealermachine', component:DealermachineComponent ,pathMatch:"prefix"},
  { path: 'dm', component:DealermachineComponent },
  { path: 'help', component: HelpComponent },
  { path: 'validators', component: ValidatorsComponent },
  { path: 'analytics', component: AnalyticsComponent },
  { path: 'about', component: AboutComponent },
  { path: 'faqs', component: FaqsComponent },
  { path: 'login', component: LoginComponent },
  { path: 'collections', component: CollectionsComponent},
  { path: 'mint', component: MintComponent },
  { path: 'miner', component: MintComponent },
  { path: 'keys', component: KeysComponent },
  { path: 'admin', component: AdminComponent },
  { path: 'contest', component: ContestComponent },
  { path: 'bank', component: BankComponent },

  { path: 'raffle', component: RaffleComponent },
  { path: 'lottery', component: ContestComponent },
  { path: 'settings', component: SettingsComponent },
  { path: 'pool', component: MinerpoolComponent },
  { path: 'dispenser', component: DispenserComponent,pathMatch:"prefix" },
  { path: 'creator', component: CreatorComponent },
  { path: 'rescue', component: RescuewalletComponent },
  { path: 'rescue_wallet', component: RescuewalletComponent },
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
