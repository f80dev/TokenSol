import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";
import {$$, getParams, jsonToList, setParams, showError, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {Clipboard} from '@angular/cdk/clipboard';
import {Location} from '@angular/common'
import {MatSnackBar} from "@angular/material/snack-bar";
import {UserService} from "../user.service";
import {NgNavigatorShareService } from 'ng-navigator-share';

import {OperationService} from "../operation.service";
import {NFT} from "../../nft";
import {_prompt} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {get_in, Operation} from "../../operation";
import {parse} from "yaml";

@Component({
  selector: 'app-build-ope',
  templateUrl: './build-ope.component.html',
  styleUrls: ['./build-ope.component.css']
})
export class BuildOpeComponent implements OnInit {

  url: string = "";
  url_ope: string="https://raw.githubusercontent.com/f80dev/TokenSol/master/Server/Operations/Main_devnet.yaml";
  collections_lottery: any[]=[];
  nfts: NFT[]=[];
  collections: any={};
  collection_keys:string[]=[];
  store_collections: any[]=[];
  sources: any;
  candymachine_qrcode: string="";
  title: string="NFluenT Candy Machine";
  mails: { transfer: any; new_account: any }={transfer:"",new_account:""};
  showPrestashop: boolean=true;
  warning="";
  ope_model: Operation | any;

  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public operation:OperationService,
    public toast:MatSnackBar,
    public user:UserService,
    public dialog:MatDialog,
    public clipboardService:Clipboard,
    public router:Router,
    public _location:Location,
    public ngShare:NgNavigatorShareService
  ) {
    this.user.addr_change.subscribe(()=>{
      this.refresh();
    })
    this.operation.sel_ope_change.subscribe((ope:Operation)=>{
      this.refresh_ope(ope);
    })
  }

  ngOnInit(): void {
    if(this.user.isConnected()){
        getParams(this.routes).then((params:any)=>{
          this.operation.select(params["ope"]);
          this.refresh();
        })
    } else {
      this.user.login("Se connecter pour accèder à la gestion des opérations");
    }
  }

  refresh () {
    if(this.operation.sel_ope) this.refresh_ope(this.operation.sel_ope);
  }

  save_operation(){
    localStorage.setItem("operation",this.operation.sel_text);
  }

  load_operation(){
    let text=localStorage.getItem("operation");
    if(text){
      this.operation.sel_ope=parse(text);
      this.operation.sel_text=text;
    }
  }


  refresh_ope(ope:Operation) {
    if(!ope)return;
    this._location.replaceState("/build","ope="+ope.id,true);

    if(!this.operation.sel_ope)return;

    this.mails={
      new_account:get_in(this.operation.sel_ope,"new_account.mail","mail standard"),
      transfer:get_in(this.operation.sel_ope,"transfer.mail","mail standard")
    }

    $$("Mise a jour des liens avec "+ope.id)

    this.network.wait("Récupération des NFTs issue des sources",500);
    this.network.get_nfts_from_operation(this.operation.sel_ope.id).subscribe((r:any)=>{
      this.network.wait("")
      this.nfts=[]
      this.collection_keys=[];
      this.sources=r.sources;
      for(let _nft of r.nfts){
        let nft:NFT=_nft;
        nft.price=nft.price  || 0;
        if(nft.collection){
          let k=nft.collection!.id;
          if(k && nft.supply>0){
            if(!this.collections.hasOwnProperty(k))this.collections[k]=0;
            if(this.collection_keys.indexOf(k)==-1)this.collection_keys.push(k);
            this.collections[k]=this.collections[k]+nft.supply;
            this.nfts.push(nft);
          }
        } else {
          this.nfts.push(nft);
        }

      }

      if(this.operation.sel_ope){
        this.showPrestashop=!(this.operation.sel_ope.store?.prestashop==null);
        let ope=this.operation.sel_ope.id;

        if(this.operation.sel_ope.lottery){
          let url=this.operation.sel_ope.lottery.application.replace("$nfluent_appli$",environment.appli)+"?ope="+ope+"&toolbar=false";
          this.operation.sel_ope.lottery.application=url;
          this.operation.sel_ope.lottery.iframe_code="<iframe src='"+url+"&mode=iframe'></iframe>";
          this.operation.sel_ope.lottery.image_code="<img src='"+this.network.server_nfluent+"/api/get_new_code/"+ope+"/?format=qrcode'>";
        }

        if(this.operation.sel_ope && this.operation.sel_ope.validate && this.operation.sel_ope.validate.application){
          this.operation.sel_ope.validate.application=this.operation.sel_ope.validate.application.replace("$nfluent_appli$",environment.appli);
        }

        if(this.operation.sel_ope.store){
          this.store_collections=this.operation.sel_ope.store.collections;
        }

        // let _c:any=null;
        // for(_c of $event.value.store.collections){
        //   if(!_c.hasOwnProperty("price"))
        //     _c.price=find_collection(this.operation.sel_ope,_c.name)?.price; //On va chercher le prix
        //   this.store_collections.push(_c);
        // }

        this.candymachine_qrcode=this.network.server_nfluent+"/api/qrcode/?code="+encodeURIComponent(this.get_url_for_appli("cm",{airdrop:false}))+"&scale=13";
      }

    },(err:any)=>{
      this.network.wait();
      showError(this,err);
    });
  }


  upload_operation($event: any) {
    this.network.upload_operation($event.filename,$event.file).subscribe((r:any)=>{
      showMessage(this,"Opération importée");
      this.refresh();
    })
  }


  new_model() {
    open(environment.appli+"/assets/new_operation.yaml","blank","");
  }

  delete_ope() {
    if(this.operation.sel_ope)
      open(this.network.server_nfluent+"/api/operations/"+this.operation.sel_ope.id+"?format=file","_blanck");
  }

  send_mail(user="") {
    this.network.send_mail_to_validateur(this.operation.sel_ope,user).subscribe(()=>{
      showMessage(this,"Notifications envoyées");
    });
  }

  async update_url_ope() {
    let rep=await _prompt(this,
      "Utiliser une opération depuis un lien web",
      "https://raw.githubusercontent.com/f80dev/TokenSol/master/Server/Operations/Main_devnet.yaml",
      "Saisissez l'url du fichier d'opération","text")
    this.operation.select("b64:"+btoa(rep));
  }

  download_ope() {
    let body={
      "filename":"config.yaml",
      "content":this.operation.sel_text,
      "type":"application/yaml"
    }
    this.network.upload(body,"server").subscribe((r:any)=>{
      //this.network.server_nfluent + "/api/configs/" + this.sel_config!.id + "/?format=file"
      open(r.url, "download");
    })

    if(this.operation.sel_ope)
      open(this.network.server_nfluent+"/api/operations/"+this.operation.sel_ope.id,"");
  }


  share_link(appli:string,title:string,text:string) {
    this.refresh();
    let url=appli.startsWith("http") ? appli : this.get_url_for_appli(appli);
    this.ngShare.share({
      title: title,
      text: text,
      url: url
    })
      .then( (response:any) => {console.log(response);},()=>{
        this.clipboardService.copy(url);
      })
      .catch( (error:any) => {
        this.clipboardService.copy(url);
      });
  }


  get_url_for_appli(appli:string,_d:any={}):string {
    if(!this.operation.sel_ope)return "";
    _d.toolbar=false
    _d.ope=this.operation.sel_ope.id;
    _d.visual=get_in(this.operation.sel_ope,"branding.splash_visual",null);
    _d.claim=get_in(this.operation.sel_ope,"branding.claim",null);
    _d.appname=get_in(this.operation.sel_ope,"branding.appname",null);
    return environment.appli+"/"+appli+"?"+setParams(_d);
  }

  open_appli(appli:string,add_param:any={}) {
    // if(this.nft_filter_by_account(this.nfts,this.user.addr)==0){
    //   showMessage(this,"le compte sélectionné ne peut transféré aucun NFT issue de la source")
    //   return;
    // }
    if(this.operation.sel_ope){
      if(appli=="validate" && (!this.operation.sel_ope.validate?.users || this.operation.sel_ope.validate?.users.length==0)){
        _prompt(this,"Nom du validateur","dudule").then((name:string)=>{
          appli="autovalidate";
          add_param["validator_name"]=name;
          add_param["network"]=this.operation.sel_ope!.network
          add_param["authentification"]=this.operation.sel_ope!.validate?.authentification
          add_param["collections"]=this.operation.sel_ope!.validate?.filters.collections
          open(this.get_url_for_appli(appli,add_param),"_self");
        })
        return;
      }
      this.refresh();
      open(this.get_url_for_appli(appli,add_param),"_self");
      }
  }

  edit_ope() {
    if(this.operation.sel_ope){
      let url="https://codebeautify.org/yaml-editor-online?url="+encodeURIComponent(this.network.server_nfluent+"/api/getyaml/"+this.operation.sel_ope.id+"/txt/?dir=./Operations");
      open(url,"editor");
    }
  }

  send_prestashop(id:string) {
    this.network.wait("Transfert vers prestashop",60);
    this.network.export_to_prestashop(id,null).subscribe((r:any)=>{
      this.network.wait("");
      showMessage(this,"NFTs transférés")
    });
  }

  analyse_order(id:string) {
    this.network.wait("Analyse des commandes",60);
    this.network.analyse_prestashop_orders(id).subscribe((r:any)=>{
      this.network.wait("");
      showMessage(this,"NFTs transférés")
    });
  }

  open_miner() {
    this.router.navigate(["miner"],{queryParams:{ope:this.operation.sel_ope?.id,toolbar:true}})
  }

  open_validate() {
    if(this.operation.sel_ope){
      let params=setParams({
        toolbar:false,
        authentification:this.operation.sel_ope.validate?.authentification,
        collections:this.operation.sel_ope.validate?.filters.collections,
        ope:this.operation.sel_ope.id
      })
      let url=environment.appli+"/autovalidate?"+params;
      if(this.operation.sel_ope.validate && this.operation.sel_ope.validate?.users.length>0){
        url=this.operation.sel_ope.validate!.application+"?"+setParams({
          toolbar:false,
          ope:this.operation.sel_ope.id
        })
      }

      this.open_appli(url,'_self');
    }
  }

  nft_filter_by_account(nfts:NFT[],addr: string,operation="transfer") {
    //Compte sur combien de NFT, addr peut effectuer l'operation operation
    let rc=0;
    for(let nft of nfts){
      if(nft.owner=="" || nft.owner==addr)rc=rc+1;
      //TODO ajouter ici les roles par rapport à la collection
    }
    return rc;
  }

  showMessages(section: string):string {
    return jsonToList(get_in(this.operation.sel_ope,section+".messages",{}));
  }

  async update_ope($event: any) {
    let r=await _prompt(this,"Effacer l'opération courrante ?","","","vrai/faux","Remplacer","Annuler",true).catch(()=>{
      this.ope_model=this.ope_model ? null : {};
    });
    if(r=="yes"){
      this.ope_model=$event;
      this.operation.sel_ope=$event;
      this.refresh_ope($event);
    }
  }
}
