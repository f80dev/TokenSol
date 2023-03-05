import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {setParams, showError, showMessage} from "../../tools";
import {NetworkService} from "../network.service";
import {environment} from "../../environments/environment";
import {Clipboard} from "@angular/cdk/clipboard";
import {NgNavigatorShareService} from "ng-navigator-share";

interface ConfigServer {
  Server:string
  Client:string
  Database_Server:string
  Database_Name:string
  Upload_Folder:string
  Database:{
    tokens:number
    validators:number
    mintpool:number
  }
}

@Component({
  selector: 'app-admin',
  templateUrl: './admin.component.html',
  styleUrls: ['./admin.component.css']
})
//test http://127.0.0.1:4200/admin
export class AdminComponent implements OnInit {
  server_addr="";
  appli_addr="";
  db_addr="";
  db_login:string=""
  db_password=""
  setup_server="";
  setup_client="";
  activity_report="";
  debug_mode: boolean=false;
  first_install:  boolean=true;
  server_config: ConfigServer | undefined;
  creator_title: string = "Générateur de visuels NFTs";
  code_creator: string = "";
  code_miner: string = "";
  intro_visual: string = "https://cdn.pixabay.com/photo/2018/02/06/22/43/painting-3135875_960_720.jpg";
  intro_claim: string = "Fabriquer vos séries NFT en quelques minutes";
  intro_appname:string="TokenForge Design";
  networks: any;
  stockages:any;
  sel_networks: any[]=[];
  sel_stockage:any;
  urls: any[] = [];
  w="550px";


  constructor(
    public user:UserService,
    public network:NetworkService,
    public clipboard:Clipboard,
    public ngShare:NgNavigatorShareService
  ) {
    this.reset();
  }

  ngOnInit(): void {

    this.user.login("Se connecter pour accèder aux commandes d'administration");
    this.load_values();
    this.update_code_creator();
    this.network.info_server().subscribe((infos:any)=>{
      this.server_config=infos;
      this.networks=this.network.config["NETWORKS"].map((x:any)=>{return {label:x,value:x}});
      this.stockages=[
        {label:"Infura",value:"infura"},
        {label:"Serveur",value:"server"},
        {label:"Base",value:"db-server-nfluent"}
      ]
    },(err)=>{
      showMessage(this,"Problème de connexion serveur")
      showError(this,err);

    })
  }

  load_values(){
    this.server_addr=localStorage.getItem("server_addr") || this.server_addr;
    this.appli_addr=localStorage.getItem("appli_addr") || this.appli_addr;
    this.db_addr=localStorage.getItem("db_addr") || this.db_addr;
    this.db_login=localStorage.getItem("db_login") || this.db_login;
    this.db_password=localStorage.getItem("db_password") || this.db_password;
    this.refresh()
  }

  refresh(saveValue=true) {
    if(saveValue){
      localStorage.setItem("server_addr",this.server_addr);
      localStorage.setItem("appli_addr",this.appli_addr);
      localStorage.setItem("db_addr",this.db_addr);
      localStorage.setItem("db_login",this.db_login);
      localStorage.setItem("db_password",this.db_password);
    }
    this.update_code_creator()
    let port=this.server_addr.indexOf(":")>1 ? this.server_addr.split(":")[2] : "80";
    let s="firewall-cmd --permanent --zone=public --add-port="+port+"/tcp<br><br>";

    if(this.first_install) {
      s = s + "cd /root<br>";
      for(let dir of ["Server","Server/Operations","Server/Configs","Server/Fonts","Server/temp"])
        s=s+"mkdir "+dir+"<br>";
      s=s+"<br>";
    } else {
      s=s+"docker rm -f tokensol<br>";
    }
    s=s+"docker pull f80hub/tokensol<br><br>";
    let db_addr=this.db_addr.replace("://","://"+this.db_login+":"+this.db_password+"@");
    s=s+"docker run --restart=always -v /root/Server/Configs:/Configs -v /root/Server/Fonts:/Fonts " +
      "-v /root/Server/Operations:/Operations -v /root/Server/temp:/temp $cert -p 4242:4242 --name tokensol " +
      "-d f80hub/tokensol:latest python3 app.py "+this.server_addr+" "+
      this.appli_addr+" "+db_addr+" "+this.activity_report+" debug";

    if(this.server_addr.startsWith("https")){
      s=s.replace("$cert","-v /root/certs:/certs");
      s=s+" ssl";
    } else {
      s=s.replace("$cert","");
    }
    if(!this.debug_mode)s=s.replace(" debug "," ")
    this.setup_server=s;

    this.setup_client=this.appli_addr+"/?param="+setParams({server:this.server_addr});
    this.update_code_creator();
  }

  reset() {
    this.server_addr=environment.server;
    this.appli_addr=environment.appli;
    this.db_login="root";
    this.db_password="hh4271";
    this.activity_report="contact@nfluent.io";
    this.refresh(false);
  }

  test_server() {

  }

  open_appli(url:any) {
    open(url.url,"Test application")
  }

  update_code_creator() {
    this.urls=[];
    let network_list=this.sel_networks.map((x:any)=>{return(x.value)}).join(",");
    let url=this.appli_addr+"/creator?param="+setParams({
      toolbar:false,
      title_form:this.creator_title,
      claim:this.intro_claim,
      visual:this.intro_visual,
      appname:this.intro_appname,
      networks:network_list,
      stockage:this.sel_stockage
    })
    this.urls.push({title:"Création des NFT", url:url})

    url=this.appli_addr+"/mint?param="+setParams({
      toolbar:false,
      title_form:this.creator_title,
      claim:this.intro_claim,
      visual:this.intro_visual,
      appname:this.intro_appname,
      networks:network_list,
      stockage:this.sel_stockage
    })
    this.urls.push({title:"Minage des NFT", url:url})

    url=this.appli_addr+"/?param="+setParams({
      toolbar:true,
      visual:this.intro_visual,
      appname:this.intro_appname,
    })
    this.urls.push({title:"Application", url:url})

    url=this.appli_addr+"/?param="+setParams({
      toolbar:true,
      appname:"TokenForge",
    })
    this.urls.push({title:"Token Forge", url:url})


  }

  copy_appli(url: any) {
    this.clipboard.copy(url.url);
    showMessage(this,"Le lien est disponible dans le presse papier")
  }

  share_appli(url: any) {
    this.ngShare.share({
      title: url.title,
      text: url.title,
      url: url.url
    })
  }
}
