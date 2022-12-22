import {ActivatedRoute, Router} from "@angular/router";
import {AfterContentInit, Component, HostListener, OnInit} from '@angular/core';
import {BreakpointObserver, Breakpoints} from '@angular/cdk/layout';
import {Observable} from 'rxjs';
import {map,shareReplay } from 'rxjs/operators';
import {UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {NETWORKS} from "../definitions";
import {Location} from "@angular/common";
import {MetabossService} from "./metaboss.service";
import {$$, getBrowserName, getParams, showMessage} from "../tools";
import {OperationService} from "./operation.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {MatSelectChange} from "@angular/material/select";
import {DeviceService} from "./device.service";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements AfterContentInit {
  title = environment.appname;
  version=environment.version;
  showSplash=true;

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );
  networks=NETWORKS;
  toolbar_visible: string="true";
  appname:string=environment.appname;
  claim:string="";
  visual:string="./assets/forge.jpg";


  constructor(
    private breakpointObserver: BreakpointObserver,
    public user:UserService,
    public network_service:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public _location:Location,
    public toast:MatSnackBar,
    public operation:OperationService,
    public metaboss:MetabossService,
    public device:DeviceService
  ) {
  }

  @HostListener('window:resize', ['$event'])
  onResize(event:any) {
    this.device.resize(event.target.innerWidth);
  }


  init_form(){
    setTimeout(()=>{this.showSplash=false;},3000);
    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("server")){
        this.network_service.server_nfluent=params["server"];
      }

      this.network_service.network=params["network"] || "elrond-devnet";
      this.visual=params["visual"] || environment.splash_visual;
      this.appname=params["appname"] || environment.appname;
      this.claim=params["claim"] || environment.claim;

      this.metaboss.init_keys(this.network_service.network);

      if(getBrowserName()=="firefox"){
        showMessage(this,"Le fonctionnement de TokenForge est optimisé pour Chrome, Edge ou Opéra. L'usage de Firefox peut entraîner des dysfonctionnement mineurs",8000,()=>{},"Ok");
      }
      if(params.hasOwnProperty("addr") || params.hasOwnProperty("miner")){
        this.user.init(params["addr"] || params["miner"]);
      } else {
        let key=localStorage.getItem("addr") || "";
        if(key.length>0){
          $$("Récupération de la clé "+key+" depuis les cookies")
          this.user.init(key);
        }
      }

      this.network_service.version=params["version"] || "main";
      if(params.hasOwnProperty("toolbar")){
        this.toolbar_visible=params["toolbar"];
      }
      else {
        this.toolbar_visible="true";
      }

    }).catch(()=>{
      debugger
    });
  }

  logout(){
    this.user.disconnect();
    this.router.navigate(["about"]);
  }


  login() {
    this.user.connect().then((addr)=>{this.router.navigate(["wallet"]);})
  }


  update_network() {
    this.network_service.complement="("+this.operation.sel_ope?.store?.prestashop?.server+")";
    this.metaboss.init_keys(this.network_service.network,false);
  }


  refresh_ope($event: MatSelectChange) {
    if(this._location.path(true).indexOf('/build')>-1){
      this._location.replaceState("/build","ope="+$event.value.id,true);
    }
    this.operation.sel_ope_change.next($event.value);
  }

  ngAfterContentInit(): void {
    setTimeout(()=>{
      this.init_form();
    },10)

  }

}

