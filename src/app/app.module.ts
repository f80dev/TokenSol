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
import {MatTabsModule} from "@angular/material/tabs";
import { PromptComponent } from './prompt/prompt.component';
import {MAT_DIALOG_DATA, MatDialogModule} from "@angular/material/dialog";
import {MatFormFieldModule} from "@angular/material/form-field";
import {MatSelectModule} from "@angular/material/select";
import {FormsModule} from "@angular/forms";
import { SafePipe } from './safe.pipe';
import {MatProgressSpinnerModule} from "@angular/material/progress-spinner";
import {NgxJsonViewerModule} from "ngx-json-viewer";

@NgModule({
  declarations: [
    AppComponent,
    HelpComponent,
    AboutComponent,
    BuyComponent,
    FaucetComponent,
    NftsComponent,
    MywalletComponent,
    PromptComponent,
    SafePipe,

  ],
  imports: [
    BrowserModule,
    BrowserAnimationsModule,
    SolWalletsModule,
    HttpClientModule,
    MatDialogModule,
    NgxJsonViewerModule,
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
    }),
    MatTabsModule,
    MatFormFieldModule,
    MatSelectModule,
    FormsModule,
    MatProgressSpinnerModule
  ],
  providers: [{provide: MAT_DIALOG_DATA, useValue: {hasBackdrop: false}}],
  bootstrap: [AppComponent]
})
export class AppModule { }
