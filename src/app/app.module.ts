import { NgModule } from '@angular/core';
import { BrowserModule } from '@angular/platform-browser';

import { AppComponent } from './app.component';
import { BrowserAnimationsModule } from '@angular/platform-browser/animations';
import {SolWalletsModule} from "angular-sol-wallets";
import {HttpClientModule} from "@angular/common/http";
import { AppRoutingModule } from './app-routing.module';

import {MatIconModule} from "@angular/material/icon";
import {MatToolbarModule} from "@angular/material/toolbar";

import { LayoutModule } from '@angular/cdk/layout';
import { MatButtonModule } from '@angular/material/button';
import { MatSidenavModule } from '@angular/material/sidenav';
import { MatListModule } from '@angular/material/list';
import { HelpComponent } from './help/help.component';
import { AboutComponent } from './about/about.component';
import { BuyComponent } from './buy/buy.component';
import { FaucetComponent } from './faucet/faucet.component';
import { NftsComponent } from './nfts/nfts.component';
import { MywalletComponent } from './mywallet/mywallet.component';
import { ServiceWorkerModule } from '@angular/service-worker';
import { environment } from '../environments/environment';

@NgModule({
  declarations: [
    AppComponent,
    HelpComponent,
    AboutComponent,
    BuyComponent,
    FaucetComponent,
    NftsComponent,
    MywalletComponent,

  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    SolWalletsModule,
    HttpClientModule,
    AppRoutingModule,
    MatIconModule,
    MatToolbarModule,
    LayoutModule,
    MatButtonModule,
    MatSidenavModule,
    MatListModule,
    ServiceWorkerModule.register('ngsw-worker.js', {
      enabled: environment.production,
      // Register the ServiceWorker as soon as the application is stable
      // or after 30 seconds (whichever comes first).
      registrationStrategy: 'registerWhenStable:30000'
    })
  ],
  providers: [],
  bootstrap: [AppComponent]
})
export class AppModule { }
