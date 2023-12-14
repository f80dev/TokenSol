import { Component, OnInit } from '@angular/core';
import {UserService} from "../user.service";
import {$$, analyse_params, getParams, jsonToList, setParams, showError, showMessage} from "../../tools";
import {NetworkService} from "../network.service";
import {environment} from "../../environments/environment";
import {Clipboard} from "@angular/cdk/clipboard";
import {NgNavigatorShareService} from "ng-navigator-share";
import {Router} from "@angular/router";
import {_prompt} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {MatSnackBar} from "@angular/material/snack-bar";
import {wait_message} from "../hourglass/hourglass.component";


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
  server_config: any ;

  networks: any;
  stockages:any;
  urls: any[] = [];
  w="550px";
  max_url_len: number=0;

  config_appli:any={
    intro_visual: "https://cdn.pixabay.com/photo/2018/02/06/22/43/painting-3135875_960_720.jpg",
    intro_claim: "Fabriquer vos séries NFT en quelques minutes",
    intro_appname:"TokenForge Design",
    creator_title: "Générateur de visuels NFTs",
    sel_stockage:["infura"],
    sel_key:environment.admin.default_miner,
    sel_col:environment.admin.default_collection,
    sel_stockage_document:["infura"],
    sel_networks:environment.admin.default_networks.split(","),
    merchant_name: environment.merchant.name,
    price:environment.admin.default_price,
    fiat_price:environment.admin.default_fiat_price,
    currency:environment.merchant.currency,
    country:environment.merchant.country,
    merchant_id:environment.merchant.id,
    wallet: {
      address: environment.merchant.wallet.address,
      unity: environment.merchant.wallet.unity,
      token: environment.merchant.wallet.token,
    }
  };
  sel_url: any=null;
  rows: any[]=[];
  sel_filter: string = "temp*";
  delay: number = 10;
  files: any[]=[];
  nb_selected_file: number=0;
  message="";
  bank_properties=[
    {label: "Réseau",value:"elrond-devnet",name:"network"},
    {label: "Montant de la recharge",value:"1",name:"bank.refund",type:"number"},
    {label: "Titre",value:"Rechargement",name:"bank.title"},
    {label: "Limite par jour",value:"2",name:"bank.limit"},
    {label: "Base d'historisation",value:"db-server-nfluent",name:"bank.histo"},
    {label: "Token",value:"",name:"bank.token"},

    {label: "Style",value:"nfluent-dark.css",name:"style"},
    {label: "Nom de l'application",value:"Bank",name:"appname"},
    {label: "Fond d'écran",value:"https://s.f80.fr/assets/wood.jpg",name:"bank.token"},
    {label: "FavIcon",value:"favicon.png",name:"favicon"},
    {label: "Splash Screen",value:"https://nftlive.nfluent.io/assets/logo_mvx.jpg",name:"visual"},
    {label: "Claim",value:"",name:"claim"},
  ];


  constructor(
      public user:UserService,
      public toast:MatSnackBar,
      public network:NetworkService,
      public clipboard:Clipboard,
      public dialog:MatDialog,
      public ngShare:NgNavigatorShareService,
      public router:Router
  ) {
    this.reset();
  }

  ngOnInit(): void {
    this.user.login("Se connecter pour accèder aux commandes d'administration");
    wait_message(this,"Chargement des informations",true);
    this.network.info_server().subscribe((infos:any)=>{
      wait_message(this);
      this.server_config=infos;
      this.refresh_file_selection();
      this.networks=this.network.config["NETWORKS"].map((x:any)=>{return {label:x,value:x}});
      this.stockages=this.network.stockage_available;

      this.load_values();
    },(err:any)=>{
      showMessage(this,"Problème de connexion serveur")
      showError(this,err);
      wait_message(this);
    })
  }

  load_values(){
    this.server_addr=localStorage.getItem("server_addr") || this.server_addr;
    this.appli_addr=localStorage.getItem("appli_addr") || this.appli_addr;
    this.db_addr=localStorage.getItem("db_addr") || this.db_addr;
    this.db_login=localStorage.getItem("db_login") || this.db_login;
    this.db_password=localStorage.getItem("db_password") || this.db_password;
    if(localStorage.getItem("config_appli")){
      this.config_appli= JSON.parse(localStorage.getItem("config_appli") || "{}");
      $$("Récupération des valeurs",this.config_appli);
      if(!this.config_appli.sel_stockage){this.config_appli.sel_stockage=this.stockages[0];}
      if(!this.config_appli.sel_stockage_document)this.config_appli.sel_stockage_document=this.stockages[0];
    }
    this.refresh()
  }

  jsonToString(obj:any,sep="\n"){
    let s=""
    for(let k of Object.keys(obj)){
      s=s+k+": "+obj[k]+sep
    }
    return s
  }

  refresh(saveValue=true) {
    //if(this.config_appli.appli_addr.endsWith("/"))this.config_appli.appli_addr=this.config_appli.appli_addr.substring(0,this.config_appli.appli_addr.length-1);
    if(saveValue){
      localStorage.setItem("server_addr",this.server_addr);
      localStorage.setItem("appli_addr",this.appli_addr);
      localStorage.setItem("db_addr",this.db_addr);
      localStorage.setItem("db_login",this.db_login);
      localStorage.setItem("db_password",this.db_password);
      localStorage.setItem("config_appli",JSON.stringify(this.config_appli))
    }
    //this.update_code_creator()
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

    this.setup_client=this.appli_addr+"/?"+setParams({server:this.server_addr});
    //this.update_code_creator();
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

  to_localhost(url:string) : string {
    let rc=url;
    let domain=url.split("://")[1].split("/")[0].split("?")[0]
    rc=url.replace("https://"+domain,"http://localhost:4200")
    return rc;
  }

  open_appli(obj:any,mode="standard") {
    if(mode=="local"){
      obj.url=this.to_localhost(obj.url);
    }
    this.copy_appli(obj.url);
    open(obj.url,"Test application")
  }


  update_code_creator() {
    this.urls=[];
    if(this.appli_addr.endsWith("/"))this.appli_addr=this.appli_addr.substring(0,this.appli_addr.length-1);
    let url_len=0;
    let first_network=this.network.networks_available[0];
    if(this.config_appli.sel_networks.length>0)first_network=this.config_appli.sel_networks[0];

    var obj:any={
      toolbar:false,
      title_form:this.config_appli.creator_title,
      claim:this.config_appli.intro_claim,
      visual:this.config_appli.intro_visual,
      appname:this.config_appli.intro_appname,
      networks:this.config_appli.sel_networks.join(","),
      stockage:this.config_appli.sel_stockage,
      stockage_document:this.config_appli.sel_stockage_document,
      price:this.config_appli.price,
      fiat_price:this.config_appli.fiat_price,

      merchant:{
        name:this.config_appli.merchant_name,
        currency:this.config_appli.currency,
        country:this.config_appli.country,
        id:this.config_appli.merchant_id,
        wallet:{
          address:this.config_appli.wallet.address,
          unity:this.config_appli.wallet.unity,
          token:this.config_appli.wallet.token,
        }
      }
    }

    var simple={...obj, }                                //spread syntax voir https://www.javascripttutorial.net/object/3-ways-to-copy-objects-in-javascript/
    this.urls.push({
      title:"Création des NFT avec minage",
      description: "Ouverture sur la création de NFT",
      url:this.config_appli.appli_addr+"/creator?"+setParams(simple),
      show_key:true,
      max_blockchain:2
    })

    simple.networks=[]
    this.urls.push({
      title:"Création des NFT sans minage",
      description: "Ouverture sur la création de NFT",
      url:this.config_appli.appli_addr+"/creator?"+setParams(simple),
      show_key:false,
      max_blockchain:0
    })

    this.urls.push({
      title:"Minage des NFT",
      description: "Ouverture sur le minage, Une seul plateforme de stockage",
      url:this.config_appli.appli_addr+"/mint?"+setParams(obj),
      show_key:true,
      max_blockchain:2
    })
    url_len=Math.max(url_len,setParams(obj).length);


    let miner=""
    if(this.config_appli.sel_key)miner=this.config_appli.sel_key.indexOf(":")==-1 ? this.config_appli.sel_key : this.config_appli.sel_key.split(":")[1]
    //Tokendoc
    this.urls.push({
      title:"TokenDoc",
      description:"application de tokenisation de document",
      url:this.config_appli.appli_addr+"/tokendoc?"+setParams({
        stockage:obj.stockage,
        stockage_document:obj.stockage_document,
        network:first_network,
        miner: miner,
        claim: this.config_appli.intro_claim,
        appname:this.config_appli.intro_appname,
        collection:this.config_appli.sel_col,
      }),
      max_blockchain:1,
      show_key:true
    })

    delete obj.stockage;
    delete obj.stockage_document;
    obj.toolbar=true;
    this.urls.push({
      title:this.config_appli.intro_appname,
      description: "",
      url:this.appli_addr+"/?"+setParams(obj),
      max_blockchain:2
    })
    url_len=Math.max(url_len,setParams(obj).length);

    obj.appname="TokenForge";
    obj.networks=this.networks;
    this.urls.push({
      title:obj.appname,
      description: "Application standard",
      url:this.config_appli.appli_addr+"/?"+setParams(obj),
    })
    url_len=Math.max(url_len,setParams(obj).length);

    obj.appname="TokenForge Devnet";
    obj.networks="elrond-devnet,polygon-devnet"
    this.urls.push({
      title:obj.appname,
      description: "application standard limitée aux Devnet",
      url:this.config_appli.appli_addr+"/?"+setParams(obj),
      show_key:false,
      max_blockchain:2
    })

    obj.appname="NFTlive Devnet";
    obj.networks="elrond-devnet,polygon-devnet"
    this.urls.push({
      title:obj.appname,
      description: "NFTLive limitée aux Devnet",
      url:this.config_appli.appli_addr+"/nftlive/?"+setParams(obj),
      show_key:true,
      max_blockchain:1
    })
    url_len=Math.max(url_len,setParams(obj).length);

    for(let url of this.urls){
      let p=url.url.split("p=")[1]
      p=analyse_params(decodeURIComponent(p));
      url.read_params=JSON.stringify(p);
    }

    this.max_url_len=url_len;
    if(!this.sel_url)this.sel_url=this.urls[0];
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

  update_key($event: any) {
    this.config_appli.sel_key=$event;
  }

  navigate_to_key() {
    this.router.navigate(["keys"]);
  }

  async register_email() {
    let email=await _prompt(this,"Email de l'utilisateur","","Son code d'accès lui sera envoyé","text","Envoyer","Annuler",false);
    this.network.registration(email).subscribe(()=>{
      showMessage(this,"Code d'accès envoyé")
      this.refresh(true);
    })
  }

  search_intro_image() {
    _prompt(this,"Recherche d'images","painting",
        "Votre requête en quelques mots en ANGLAIS de préférence",
        "text","Rechercher", "Annuler",false).then((query:string)=>{

      this.network.search_images(query,false).subscribe((r:any)=>{
        if(r){
          _prompt(this,"Choisissez une images","","",
              "images","Sélectionner","Annuler",false,r.images).then((images:string)=>{
            this.config_appli.intro_visual=images[0];
          })
        }
      })
    })

  }

  informe_copy() {
    showMessage(this,"Lien disponible dans le presse-papier")
  }

  raz_save_local() {
    localStorage.removeItem("config_appli")
    this.refresh();
  }


  batch_import(files: any) {
    //Chargement du fichier excel
    let to_copy=""
    if (files.hasOwnProperty("filename")) files = [files]
    for (let f of files) {
      if (f.filename.endsWith("xlsx")) {
        this.network.upload_excel_file({content:f.file}).subscribe((rows:any[])=>{
          this.rows=[]
          for(let r of rows){
            r.title=r.appname

            let obj={...r}
            obj["comment"]=null
            r.read_params=JSON.stringify(obj).replace(new RegExp(",", 'g'),",\n")
            if(r.url.indexOf("?")>-1){
              r.url=r.url+"&"+setParams(obj)
            }else{
              if(r.url.endsWith("/")){
                r.url=r.url+"?"+setParams(obj)
              }else{
                r.url=r.url+"/?"+setParams(obj)
              }

            }

            to_copy=to_copy+r.url+"\t"+this.to_localhost(r.url)+"\n";
            this.rows.push(r)
          }
          this.clipboard.beginCopy(to_copy).copy()
          showMessage(this,"Fichier importé. Les liens sont disponibles dans le presse-papier");
        })
      }
    }
  }


  shorter(row: any) {
    open("https://tinyurl.com/app/?long-url="+encodeURIComponent(row.url),"shortener")
  }

  default_appli_list() {
    let url="https://github.com/f80dev/TokenSol/raw/master/Parametres%20des%20applications.xlsx";
    this.batch_import([{filename:url,file:url}]);
  }

  refresh_file_selection() {
    this.files=[];
    let filter=this.sel_filter;
    this.nb_selected_file=0
    if(filter.endsWith("*"))filter=filter.substring(0,filter.length-1);
    for(let f of this.server_config!.Uploaded_files){
      f.selected=(f.name.startsWith(filter) && f.delay>this.delay);
      if(f.selected)this.nb_selected_file=this.nb_selected_file+1;
      this.files.push(f);
    }
  }

  delete_selected_files() {
    let op=0;
    for(let f of this.files){
      if(f.selected){
        this.network.delete_file(f.name).subscribe(()=>{
          op=op+1;
          if(op>=this.nb_selected_file)this.refresh_file_selection();
        });
      }
    }
  }



  upload_on_server(directory: string,files:any[]) {
    if(typeof(files[0])!="object")files=[files];
    for(let f of files){
      this.network.upload(f,"server/"+directory).subscribe(()=>{
        showMessage(this,f.filename+" uploadé")
      })
    }
  }


  protected readonly jsonToList = jsonToList;
}
