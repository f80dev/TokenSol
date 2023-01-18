import {ActivatedRoute, Router} from "@angular/router";
import {AfterContentInit, Component, HostListener, OnInit, ViewChild} from '@angular/core';
import {BreakpointObserver, Breakpoints} from '@angular/cdk/layout';
import {Observable} from 'rxjs';
import {map,shareReplay } from 'rxjs/operators';
import {UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {NETWORKS} from "../definitions";
import {Location} from "@angular/common";
import {$$, CryptoKey, find, getBrowserName, getParams, setParams, showMessage} from "../tools";
import {OperationService} from "./operation.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {DeviceService} from "./device.service";
import {Operation} from "../operation";
import {MatSidenav} from "@angular/material/sidenav";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements AfterContentInit {
  title = environment.appname;
  version=environment.version;
  showSplash=true;
  @ViewChild('drawer', {static: false}) drawer: MatSidenav | undefined;

  isHandset$: Observable<boolean> = this.breakpointObserver.observe(Breakpoints.Handset+Breakpoints.HandsetPortrait)
    .pipe(
      map(result => result.matches),
      shareReplay()
    );

  networks=NETWORKS.map((x)=>{return {label:x,value:x}});
  toolbar_visible: string="true";
  appname:string=environment.appname;
  claim:string="";
  visual:string="./assets/forge.jpg";
  operations: any;
  selected_operation:Operation | undefined;
  sel_network:{label:string,value:string} | undefined;
  sel_addr: string="nfluent";

  constructor(
    private breakpointObserver: BreakpointObserver,
    public user:UserService,
    public network_service:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public _location:Location,
    public toast:MatSnackBar,
    public operation:OperationService,
    public device:DeviceService
  ) {
    this.operation.sel_ope_change.subscribe((ope:Operation)=>{this.selected_operation=ope;})

    this.network_service.network_change.subscribe((network_name:string)=>{
      //Resynchronize le réseau
      let index=find(this.networks,{label:network_name,value:network_name},"value");
      if(index>-1)this.sel_network=this.networks[index];
    });

    this.user.addr_change.subscribe((r:string)=>{
      this.sel_addr=r;
    })
  }

  @HostListener('window:resize', ['$event'])
  onResize(event:any) {
    this.device.resize(event.target.innerWidth);
  }


  informe_copy() {
    showMessage(this,"Adresse de "+this.user.addr+" copiée");
  }

  refill() {

  }

  open_wallet() {
    let url=environment.wallet+"/wallet/?param="+setParams({addr:this.user.addr,toolbar:true,network:this.sel_network?.value});
    open(url,"wallet");
  }


  set_key($event: string) {
    this.user.init($event).then(()=>{
      localStorage.setItem("addr",this.user.key?.address!);
    })
  }



  init_form(){
    setTimeout(()=>{this.showSplash=false;},1000);
    getParams(this.routes).then((params:any)=>{

      if(params.hasOwnProperty("server")){
        this.network_service.server_nfluent=params["server"];
      }

      let network_name=params["network"] || this.networks[0].value;
      let index=find(this.networks,{value:network_name,label:network_name},"value");
      this.network_service.network=network_name;
      this.sel_network=this.networks[index];

      this.visual=params["visual"] || environment.splash_visual;
      this.appname=params["appname"] || environment.appname;
      this.claim=params["claim"] || environment.claim;

      this.network_service.init_keys(this.network_service.network);

      if(getBrowserName()=="firefox"){
        showMessage(this,"Le fonctionnement de TokenForge est optimisé pour Chrome, Edge ou Opéra. L'usage de Firefox peut entraîner des dysfonctionnement",8000,()=>{},"Ok");
      }
      if(params.hasOwnProperty("addr") || params.hasOwnProperty("miner")){
        this.user.init(params["addr"] || params["miner"]).then(()=>{});
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
    }).catch(
        ()=>{}
    );
  }

  logout(){
    this.user.disconnect();
    this.router.navigate(["about"]);
  }


  login() {
    this.user.connect().then((addr)=>{this.router.navigate(["wallet"]);})
  }


  update_network($event:any) {
    this.network_service.complement="("+this.operation.sel_ope?.store?.prestashop?.server+")"
    this.network_service.network=$event.value;
    // this.network_service.init_keys($event.value,true).then((keys:any)=>{
    //   this.keys=keys;
    // })
  }


  refresh_ope($event:any) {
    if($event) this.operation.select($event.id);
  }


  ngAfterContentInit(): void {
      this.init_form();
  }

  close_menu() {
    this.isHandset$.subscribe((r:boolean)=>{
      if(r && this.drawer)this.drawer.toggle();
    })
  }
}

