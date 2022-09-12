import { Component, OnInit } from '@angular/core';
import {environment} from "../../environments/environment";
import {NetworkService} from "../network.service";
import {getParams, setParams, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {Clipboard} from '@angular/cdk/clipboard';
import {MatSnackBar} from "@angular/material/snack-bar";
import {UserService} from "../user.service";
import {NgNavigatorShareService } from 'ng-navigator-share';
import {NFT} from "../nfts/nfts.component";
import {OperationService} from "../operation.service";

@Component({
  selector: 'app-build-ope',
  templateUrl: './build-ope.component.html',
  styleUrls: ['./build-ope.component.css']
})
export class BuildOpeComponent implements OnInit {

  url: string = "";

  iframe_code: string="";
  image_code: string="";
  url_ope: string="";
  url_dispenser_app: string="";
  collections_lottery: any[]=[];
  nfts: NFT[]=[];
  collections: any={};
  collection_keys:string[]=[];
  url_store="";
  store_collections: any[]=[];
  sources: any;
  candymachine_qrcode: string="";
  candymachine_url: string="";
  title: string="NFluenT Candy Machine";


  constructor(
    public network:NetworkService,
    public routes:ActivatedRoute,
    public operation:OperationService,
    public toast:MatSnackBar,
    public user:UserService,
    public clipboardService:Clipboard,
    public router:Router,
    public ngNavigatorShareService: NgNavigatorShareService
  ) { }

  ngOnInit(): void {

    if(this.user.isConnected()){

      setTimeout(()=>{
        getParams(this.routes).then((params:any)=>{
          this.operation.select(params["ope"]);
          this.refresh();
        })

      },1000);
    } else {
      this.user.login();
    }
  }

  refresh () {
    if(this.operation.sel_ope)this.url_store=environment.appli+"/store?toolbar=false&ope="+this.operation.sel_ope.id;
    this.refresh_ope({value:this.operation.sel_ope});
  }


  refresh_ope($event: any) {
    if(!$event.value)return;

    if(!this.operation.sel_ope)return;


    this.network.wait("Récupération des NFTs issue des sources",500);
    this.network.get_nfts_from_operation(this.operation.sel_ope.id).subscribe((r:any)=>{
      this.network.wait("")
      this.nfts=[]
      this.collection_keys=[];
      this.sources=r.sources;
      for(let _nft of r.nfts){
        let nft:NFT=_nft;
        nft.marketplace!.price=nft.marketplace!.price  || 0;
        let k=nft.collection;
        if(k && nft.marketplace!.quantity>0){
          if(!this.collections.hasOwnProperty(k))this.collections[k]=0;
          if(this.collection_keys.indexOf(k)==-1)this.collection_keys.push(k);
          this.collections[k]=this.collections[k]+nft.marketplace!.quantity;
        }
      }

      if(this.operation.sel_ope){
        let ope=this.operation.sel_ope.id;

        if(this.operation.sel_ope.lottery){
          let url=this.operation.sel_ope.lottery.application.replace("$nfluent_appli$",environment.appli)+"?ope="+ope+"&toolbar=false";
          this.operation.sel_ope.lottery.application=url;
          this.operation.sel_ope.lottery.iframe_code="<iframe src='"+url+"&mode=iframe'></iframe>";
          this.operation.sel_ope.lottery.image_code="<img src='"+environment.server+"/api/get_new_code/"+ope+"/?format=qrcode'>";
        }

        if(this.operation.sel_ope.dispenser){
          this.url_dispenser_app=this.operation.sel_ope.dispenser.application.replace("$nfluent_appli$",environment.appli)
            +"?param="+setParams({ope:ope,toolbar:false});
        }

        if(this.operation.sel_ope.validate){
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
      }

      if(this.operation.sel_ope?.candymachine){
        this.candymachine_url=environment.appli+"/cm?param="+setParams({ope:this.operation.sel_ope.id,toolbar:false});
        this.network.qrcode(this.candymachine_url,"json").subscribe((result:any)=>{
          this.candymachine_qrcode=result.qrcode;
        })
      }
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
      open(environment.server+"/api/operations/"+this.operation.sel_ope.id+"?format=file","_blanck");
  }

  send_mail(user="") {
    this.network.send_mail_to_validateur(this.operation.sel_ope,user).subscribe(()=>{
      showMessage(this,"Notifications envoyées");
    });
  }

  update_url_ope(evt:any) {
    this.url=environment.appli+"/validate?toolbar=false&ope=b64:"+btoa(this.url_ope);
    this.network.get_operations(this.url_ope).subscribe((ope:any)=>{
      this.operation.sel_ope=ope;
      showMessage(this,"Operation chargée");
    })
  }

  download_ope() {
    if(this.operation.sel_ope)
      open(environment.server+"/api/operations/"+this.operation.sel_ope.id,"download");
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

  open_appli(href: string, target: string="_self") {
    if(this.operation.sel_ope){
      href=href.replace("$nfluent_appli$",environment.appli).replace("https://tokenfactory.nfluent.io",environment.appli);
      open(href,target);
    }
  }

  edit_ope() {
    if(this.operation.sel_ope){
      let url="https://codebeautify.org/yaml-editor-online?url="+encodeURI(environment.server+"/api/getyaml/"+this.operation.sel_ope.id+"/txt/?dir=./Operations");
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

  open_miner() {
    this.router.navigate(["miner"],{queryParams:{ope:this.operation.sel_ope?.id,toolbar:true}})
  }

  open_validate() {
    if(this.operation.sel_ope){
      let url=this.operation.sel_ope.validate!.application+"?param="+setParams({
        toolbar:false,
        ope:this.operation.sel_ope.id
      })
      this.open_appli(url,'_self');
    }
  }
}
