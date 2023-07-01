import {ActivatedRoute, NavigationEnd, Router} from "@angular/router";
import {AfterViewInit, Component, HostListener, OnInit, ViewChild} from '@angular/core';
import {UserProfil, UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {Location} from "@angular/common";
import {$$, apply_params, convert_to_list, find, getBrowserName, getParams, setParams, showMessage} from "../tools";
import {OperationService} from "./operation.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {DeviceService} from "./device.service";
import {MatSidenav} from "@angular/material/sidenav";
import {menu_items} from "./menu/menu.component";
import {StyleManagerService} from "./style-manager.service";


declare const gtag: Function;


@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements OnInit,AfterViewInit {
  @ViewChild('drawer', {static: false}) drawer: MatSidenav | undefined;

  networks:any[]=[];
  claim:string="";
  visual:string="";
  operations: any;
  sel_network:{label:string,value:string} | undefined;
  items:menu_items={
    creator:{label:"Visuels NFT",title:"",actif:true,icon:"photo",queryParam:{}},
    collections:{label:"Collections",title:"",actif:false,icon:"collections",queryParam:{}},
    keys:{label:"Clés",title:"",actif:true,icon:"key",queryParam:{}},
    mint:{label:"Miner",title:"",actif:true,icon:"build",queryParam:{}},
    build:{label:"Opérations",title:"",actif:true,icon:"edit",queryParam:{}},
    validators:{label:"Validateurs",title:"",actif:true,icon:"checkmark",queryParam:{}},
    analytics:{label:"Analytics",title:"",actif:true,icon:"analytics",queryParam:{}},
    wallet:{label:"Wallet",title:"",actif:false,icon:"dollar",queryParam:{}},
    pool:{label:"Pool de minage",title:"",actif:true,icon:"list",queryParam:{}},
    rescue:{label:"Restauration",title:"",actif:false,icon:"build_circle",queryParam:{}}, // & {'ope':operation!.sel_ope!.id,'network':network_service!.network}
    _logout:{label:"Déconnexion",title:"",actif:false,icon:"logout",queryParam:{}},
    login:{label:"Se connecter",title:"",actif:true,icon:"login",queryParam:{}},
    settings:{label:"Préférences",title:"Gérer ses préférences",actif:true,icon:"lock",queryParam:{}},
    admin:{label:"Administration",title:"",actif:true,icon:"lock",queryParam:{}},
    faqs:{label:"Questions",title:"",actif:true,icon:"quiz",queryParam:{}},
    about:{label:"A propos",title:"",actif:true,icon:"person",queryParam:{}},
  }
  status="disconnect";
  full_menu: boolean = true;
  appname: string="";

  constructor(
    public user:UserService,
    public network_service:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public _location:Location,
    public toast:MatSnackBar,
    public style:StyleManagerService,
    public operation:OperationService,
    public device:DeviceService
  ) {

    this.router.events.subscribe((event) => {
      if (event instanceof NavigationEnd) {
        gtag('config', 'G-FLYQ98Q9W9', { 'page_path': event.urlAfterRedirects });
      }
    })


    this.user.profil_change.subscribe(()=>{this.update_menu();})
    this.user.addr_change.subscribe(()=>{this.update_menu();})
    this.network_service.network_change.subscribe(()=>{this.update_menu()})

    this.device.isHandset$.subscribe((r:boolean)=>{if(r && this.drawer && this.user.toolbar_visible)this.drawer.toggle();})
    this.device.smallScreen.subscribe((r:boolean)=>{this.full_menu=!r;})

    // this.network_service.network_change.subscribe((network_name:string)=>{
    //   //Resynchronize le réseau
    //   let index=find(this.networks,{label:network_name,value:network_name},"value");
    //   if(index>-1)this.sel_network=this.networks[index];
    // });
    //
    // this.user.addr_change.subscribe((r:string)=>{this.sel_addr=r;})

    // this.network_service.config_loaded.subscribe((r:any)=>{
    //   let access_code=localStorage.getItem("access_code") || "";
    //   let email=localStorage.getItem("email") || "";
    //   this.user.setProfil(email,access_code).finally(()=>{
    //     this.init_form()
    //     this.filter_menu();
    //   });
    // },(err)=>{
    //   this.showSplash=false;
    //   this.router.navigate(["pagenotfound"]);
    // })

    this.user.profil_change.subscribe((p:UserProfil)=>{
      this.update_menu()
    })
  }

  ngAfterViewInit(): void {
    setTimeout(()=>{this.init_form();},200);
  }

  ngOnInit(): void {
    if(getBrowserName()=="firefox"){
      showMessage(this,"Le fonctionnement de TokenForge est optimisé pour Chrome, Edge ou Opéra. L'usage de Firefox peut entraîner des dysfonctionnement",8000,()=>{},"Ok");
    }
  }


  update_menu(){
    let connected=this.user.isConnected();
    this.items["settings"].actif=connected;
    this.items["keys"].actif=connected;
    this.items["build"].actif=connected;
    this.items["analytics"].actif=connected;
    this.items["login"].actif=!connected;
    this.items["pool"].actif=connected;
    this.items["_logout"].actif=connected;
    this.items["admin"].actif=connected && this.user.hasPerm("admin");
    this.status=connected ? "connected" : "disconnected";
  }


  @HostListener('window:resize', ['$event'])
  onResize(event:any) {
    this.device.resize(event.target.innerWidth);
  }

  filter_menu(){
      for(let k of Object.keys(this.items)){
        this.items[k].actif=this.items[k].actif && (this.network_service.config.Menu.split(",").indexOf(k.toLowerCase())>-1);
      }
  }



  informe_copy() {
    showMessage(this,"Adresse de "+this.user.addr+" copiée");
  }

  refill() {

  }

  open_wallet() {
    let url=environment.wallet+"/wallet/?"+setParams({addr:this.user.addr,toolbar:true,network:this.sel_network?.value});
    open(url,"wallet");
  }


  async init_form() {
    debugger
    let params:any = await getParams(this.routes, "params", true)
    apply_params(this,params,environment)

    this.user.params = params;
    if (params.hasOwnProperty("toolbar")) {
      this.user.toolbar_visible = params["toolbar"]
    } else {
      this.user.toolbar_visible = true;  //Par défaut on ne montre pas la toolbar
    }

    this.network_service.server_nfluent = params["server"] || environment.server;

    this.user.advance_mode = params["server"] || false;
    this.user.merchant = params["merchant"] || environment.merchant;

    $$("Préparation des réseaux disponibles")
    this.network_service.networks_available = convert_to_list(params["networks"] || environment.networks_available)
    this.network_service.stockage_available = convert_to_list(params["stockage"] || environment.stockage.split(","));
    this.network_service.stockage_document_available = convert_to_list(params["stockage_document"] || environment.stockage_document)

    this.networks = this.network_service.networks_available.map((x: any) => {
      return {label: x, value: x}
    });

    // if(this.network_service.networks_available.indexOf(network_name)==-1)network_name=this.networks[0].value;
    // let index=find(this.networks,{value:network_name,label:network_name},"value");
    // if (this.networks.length > 0) {
    //   this.network_service.network = this.networks[0].value;
    //   this.sel_network = this.networks[0].value;
    //   if (params.hasOwnProperty("addr") || params.hasOwnProperty("miner")) {
    //     this.user.init(params["addr"] || params["miner"], this.network_service.network).then(() => {
    //       // this.network_service.init_keys().then(()=>{
    //       //
    //       // });
    //     });
    //   }
    // }

    this.user.addr = params["addr"]
    this.network_service.version = params["version"] || "main";

    $$("Message de disponibilité des parametres")
    this.user.params_available.next(params);

    this.update_menu();

  }

  logout(){
    this.user.logout();
    this.update_menu();
    this.router.navigate(["/"]);
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




  close_menu() {

  }

  save_mode($event:any) {
    localStorage.setItem("advance_mode",$event ? "true" : "false");
  }


  menuSelect($event: any) {
    if($event.link=="_logout"){this.logout();}
  }


  theme_mode($event: any) {
    if($event){
      this.style.setStyle("theme","nfluent-dark.css")
    } else {
      this.style.setStyle("theme","nfluent.css")
    }
  }
}

