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
import {MatInputModule} from "@angular/material/input";
import {KeysComponent} from "./keys/keys.component";
import { MintComponent } from './mint/mint.component';
import {MatProgressBarModule} from "@angular/material/progress-bar";
import { SelectkeyComponent } from './selectkey/selectkey.component';
import {MatButtonToggleModule} from "@angular/material/button-toggle";
import {MatCheckboxModule} from "@angular/material/checkbox";
import {MatSnackBarModule} from "@angular/material/snack-bar";
import { ManageComponent } from './manage/manage.component';
import { LinkComponent } from './link/link.component';
import {ClipboardModule} from "@angular/cdk/clipboard";
import { FilterPipe } from './filter.pipe';
import { AliasPipe } from './alias.pipe';
import { UploadFileComponent } from './upload-file/upload-file.component';
import { CreatorComponent } from './creator/creator.component';
import { OrderPipe } from './order.pipe';
import {MatSliderModule} from "@angular/material/slider";
import {ColorPickerModule} from "ngx-color-picker";
import {MatExpansionModule} from "@angular/material/expansion";
import { ValidateComponent } from './validate/validate.component';
import { DealermachineComponent } from './dealermachine/dealermachine.component';
import { ContestComponent } from './contest/contest.component';
import { BuildOpeComponent } from './build-ope/build-ope.component';
import { HourglassComponent } from './hourglass/hourglass.component';
import { ScannerComponent } from './scanner/scanner.component';
import {WebcamModule} from "ngx-webcam";


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
    KeysComponent,
    MintComponent,
    SelectkeyComponent,
    ManageComponent,
    LinkComponent,
    FilterPipe,
    AliasPipe,
    UploadFileComponent,
    CreatorComponent,
    OrderPipe,
    ValidateComponent,
    DealermachineComponent,
    ContestComponent,
    BuildOpeComponent,
    HourglassComponent,
    ScannerComponent

  ],
    imports: [
        BrowserModule,
        BrowserAnimationsModule,
        SolWalletsModule,
        ColorPickerModule,
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
        MatProgressSpinnerModule,
        MatInputModule,
        MatSnackBarModule,
        MatProgressBarModule,
        MatButtonToggleModule,
        MatCheckboxModule,
        ClipboardModule,
        MatSliderModule,
        MatExpansionModule,
        WebcamModule
    ],
  providers: [
    FilterPipe,AliasPipe,SafePipe,OrderPipe,
    {provide: MAT_DIALOG_DATA, useValue: {hasBackdrop: false}}
  ],
  bootstrap: [AppComponent]
})
export class AppModule { }
