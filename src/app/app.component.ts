import {ActivatedRoute, Router} from "@angular/router";
import {AfterContentInit, AfterViewInit, Component, HostListener, OnInit, ViewChild} from '@angular/core';
import {UserProfil, UserService} from "./user.service";
import {NetworkService} from "./network.service";
import {environment} from "../environments/environment";
import {Location} from "@angular/common";
import {find, getBrowserName, getParams, setParams, showMessage} from "../tools";
import {OperationService} from "./operation.service";
import {MatSnackBar} from "@angular/material/snack-bar";
import {DeviceService} from "./device.service";
import {MatSidenav} from "@angular/material/sidenav";
import {menu_items} from "./menu/menu.component";

@Component({
  selector: 'app-root',
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
export class AppComponent implements AfterContentInit {
  showSplash=true;
  @ViewChild('drawer', {static: false}) drawer: MatSidenav | undefined;

  networks:any[]=[];
  toolbar_visible: string="true";
  appname:string=environment.appname;
  claim:string="";
  visual:string="";
  operations: any;
  //selected_operation:Operation | undefined;
  sel_network:{label:string,value:string} | undefined;
  sel_addr: string="nfluent";
  items:menu_items={
    creator:{label:"Visuels NFT",title:"",actif:true,icon:"photo",queryParam:{}},
    collections:{label:"Collections",title:"",actif:true,icon:"collections",queryParam:{}},
    keys:{label:"Clés",title:"",actif:true,icon:"key",queryParam:{}},
    mint:{label:"Miner",title:"",actif:true,icon:"build",queryParam:{}},
    build:{label:"Opérations",title:"",actif:true,icon:"edit",queryParam:{}},
    analytics:{label:"Analytics",title:"",actif:true,icon:"analytics",queryParam:{}},
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

  constructor(
    public user:UserService,
    public network_service:NetworkService,
    public routes:ActivatedRoute,
    public router:Router,
    public _location:Location,
    public toast:MatSnackBar,
    public operation:OperationService,
    public device:DeviceService
  ) {

    // this.operation.sel_ope_change.subscribe((ope:Operation)=>{
    //   this.selected_operation=ope;
    //   this.items["rescue"].actif=(operation!=null && operation.sel_ope!=null && operation.sel_ope.id.length>0);
    // })

    this.device.isHandset$.subscribe((r:boolean)=>{if(r && this.drawer && this.toolbar_visible=="true")this.drawer.toggle();})
    this.device.smallScreen.subscribe((r:boolean)=>{this.full_menu=!r;})

    this.network_service.network_change.subscribe((network_name:string)=>{
      //Resynchronize le réseau
      let index=find(this.networks,{label:network_name,value:network_name},"value");
      if(index>-1)this.sel_network=this.networks[index];
    });

    this.user.addr_change.subscribe((r:string)=>{this.sel_addr=r;})

    this.network_service.config_loaded.subscribe((r:any)=>{
      let access_code=localStorage.getItem("access_code") || "";
      let email=localStorage.getItem("email") || "";
      this.user.setProfil(email,access_code).finally(()=>{
        this.init_form()
        this.filter_menu();
      });
      this.networks=this.network_service.config["NETWORKS"].map((x:any)=>{return {label:x,value:x}});
    },(err)=>{
      this.showSplash=false;
      this.router.navigate(["pagenotfound"]);
    })

    this.user.profil_change.subscribe((p:UserProfil)=>{
      this.update_menu()
    })
  }


  update_menu(){
    let connected=this.user.isConnected(true);
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
    let url=environment.wallet+"/wallet/?param="+setParams({addr:this.user.addr,toolbar:true,network:this.sel_network?.value});
    open(url,"wallet");
  }


  set_key($event: string) {
    this.user.init($event,this.network_service.network).then(()=>{
      localStorage.setItem("addr",this.user.key?.address!);
    })
  }


  init_form(){
    getParams(this.routes).then((params:any)=>{

      this.visual=params["visual"] || environment.splash_visual;
      this.appname=params["appname"] || environment.appname;
      this.claim=params["claim"] || environment.claim;

      this.load_mode();

      if(params.hasOwnProperty("server")){
        this.network_service.server_nfluent=params["server"];
      }

      let network_name=params["network"] || this.networks[0].value;
      let index=find(this.networks,{value:network_name,label:network_name},"value");
      this.network_service.network=network_name;
      this.sel_network=this.networks[index];

      if(getBrowserName()=="firefox"){
        showMessage(this,"Le fonctionnement de TokenForge est optimisé pour Chrome, Edge ou Opéra. L'usage de Firefox peut entraîner des dysfonctionnement",8000,()=>{},"Ok");
      }

      if(params.hasOwnProperty("addr") || params.hasOwnProperty("miner")){
        this.user.init(params["addr"] || params["miner"],this.network_service.network).then(()=>{
          this.network_service.init_keys(this.network_service.network);
        });
      } else {
        // let key=localStorage.getItem("addr") || "";
        // if(key.length>0){
        //   $$("Récupération de la clé "+key+" depuis les cookies")
        //   this.user.init(key);
        // }
      }

      setTimeout(()=>{this.showSplash=false;},1000);

      this.network_service.version=params["version"] || "main";
      this.toolbar_visible=params.hasOwnProperty("toolbar") ? params["toolbar"] : "true";
      this.update_menu();

    }).catch(
        ()=>{}
    );
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

  load_mode(){
    this.user.advance_mode=localStorage.getItem("advance_mode")=="true" ? true : false;
  }

  menuSelect($event: any) {
    if($event.link=="_logout"){this.logout();}
  }

  ngAfterContentInit(): void {

  }
}

