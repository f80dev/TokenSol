import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";
import {showMessage} from "../../tools";
import {ActivatedRoute} from "@angular/router";
import {MatSnackBar} from "@angular/material/snack-bar";
import {UserService} from "../user.service";
import {Location} from "@angular/common";
import { NgNavigatorShareService } from 'ng-navigator-share';
import {Clipboard} from "@angular/cdk/clipboard";

@Component({
  selector: 'app-build-ope',
  templateUrl: './build-ope.component.html',
  styleUrls: ['./build-ope.component.css']
})
export class BuildOpeComponent implements OnInit {
  sel_ope: any=null;
  url: string = "";
  url_lottery: string = "";
  opes: any[]=[];
  iframe_code: string="";
  image_code: string="";
  url_ope: string="";
  url_dispenser_app: string="";
  collections_lottery: any[]=[];
  nfts: any=[];
  collections: any={};
  collection_keys:string[]=[];

  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public toast:MatSnackBar,
    public user:UserService,
    public clipboardService:Clipboard,
    public _location:Location,
    public ngNavigatorShareService: NgNavigatorShareService
  ) { }

  ngOnInit(): void {
    this.refresh();
  }

  refresh(){
    this.user.connect("create").then((addr)=>{
      this.network.get_operations().subscribe((r:any)=>{
        this.opes=r;
        if(!this.sel_ope){
          this.sel_ope=r[r.length-1];
          this.refresh_ope({value:this.sel_ope});
        }
      })
    })
  }

  refresh_ope($event: any) {
    let ope=$event.value.id;
    let url=this.sel_ope.lottery.application.replace("$nfluent_appli$",environment.appli)+"?ope="+ope+"&toolbar=false";
    this.sel_ope.lottery.application=url;
    this.network.get_nfts_from_operation(this.sel_ope.id).subscribe((r:any)=>{
      this.nfts=[]
      this.collection_keys=[];
      for(let nft of r){
        let k=nft.collection.name;
        if(k && nft.quantity>0){
          if(!this.collections.hasOwnProperty(k))this.collections[k]=0;
          if(this.collection_keys.indexOf(k)==-1)this.collection_keys.push(k);
          this.collections[k]=this.collections[k]+nft["quantity"];
        }
      }
    })
    this.url_dispenser_app=this.sel_ope.dispenser.application.replace("$nfluent_appli$",environment.appli)+"?ope="+ope+"&toolbar=false";
    this.sel_ope.lottery.iframe_code="<iframe src='"+url+"&mode=iframe'></iframe>";
    this.sel_ope.lottery.image_code="<img src='"+environment.server+"/api/get_new_code/"+ope+"/?format=qrcode'>";
    this.sel_ope.validate.application=this.sel_ope.validate.application.replace("$tokensol$",environment.appli)+"?ope="+ope;
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
    open(environment.server+"/api/operations/"+this.sel_ope.id+"?format=file","_blanck");
    // this.network.delete_operation(this.sel_ope.code).subscribe(()=>{
    //   this.refresh();
    // });
  }

  send_mail(user="") {
    this.network.send_mail_to_validateur(this.sel_ope,user).subscribe(()=>{
      showMessage(this,"Notifications envoyées");
    });
  }

  update_url_ope(evt:any) {
    this.sel_ope={};
    this.url=environment.appli+"/validate?toolbar=false&ope=b64:"+btoa(this.url_ope);
    this.network.get_operations(this.url_ope).subscribe((ope:any)=>{
      this.sel_ope=ope;
      showMessage(this,"Operation chargée");
    })
  }

  download_ope() {
    open(environment.server+"/api/operations/"+this.sel_ope.id,"download");
  }

  share_link(url:string,title:string,text:string) {
    this.ngNavigatorShareService.share({
      title: title,
      text: text,
      url: url
    })
      .then( (response) => {console.log(response);},()=>{
        this.clipboardService.copy(url);
      })
      .catch( (error) => {
        this.clipboardService.copy(url);
      });
  }

  open_appli(href: string, target: string) {
    open(href,target);
  }

  edit_ope() {
    let url="https://codebeautify.org/yaml-editor-online?url="+encodeURI(environment.server+"/api/getyaml/"+this.sel_ope.id+"/txt/?dir=./Operations");
    open(url,"editor");
  }
}
