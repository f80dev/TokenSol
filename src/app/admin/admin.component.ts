import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {setParams, showError, showMessage} from "../../tools";
import {NetworkService} from "../network.service";

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

  constructor(
    public user:UserService,
    public network:NetworkService
  ) {
    this.reset();
  }

  ngOnInit(): void {
    this.user.login("Se connecter pour accèder aux commandes d'administration");
    this.load_values();
    this.network.info_server().subscribe((infos:any)=>{
      this.server_config=infos;
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
  }

  reset() {
    this.server_addr="https://server.f80lab.com:4242";
    this.appli_addr="https://tokenforge.nfluent.io:4200";
    this.db_addr="mongodb://server.f80lab.com:27027";
    this.db_login="root";
    this.db_password="hh4271";
    this.activity_report="contact@nfluent.io";
    this.refresh(false);
  }

  test_server() {

  }

  open_appli() {
    open(this.appli_addr,"Test application")
  }
}
