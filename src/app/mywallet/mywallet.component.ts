import {Component, DoCheck, Input, OnDestroy, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {$$, getParams, isLocal, newCryptoKey, setParams, showError, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {environment} from "../../environments/environment";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Observable, Subject} from "rxjs";
import {Location} from "@angular/common";
import {NFT} from "../../nft";
import {Collection, newCollection, Operation} from "../../operation";
import {UserService} from "../user.service";
import {Clipboard} from "@angular/cdk/clipboard";
import {Socket} from "ngx-socket-io";

//Test : http://localhost:4200/wallet?addr=LqCeF9WJWjcoTJqWp1gH9t6eYVg8vnzUCGBpNUzFbNr&toolbar=false
@Component({
  selector: 'app-mywallet',
  templateUrl: './mywallet.component.html',
  styleUrls: ['./mywallet.component.css']
})
export class MywalletComponent implements OnInit,OnDestroy {
  nfts: NFT[]=[];
  indexTab: number=0;
  url_key: any="";
  showDetail=false;

  @Input("filter") filter="";

  private trigger: Subject<void> = new Subject<void>();
  private nextWebcam: Subject<boolean|string> = new Subject<boolean|string>();
  photos_to_send: string[]=[];
  qrcode:string="";
  network:string=""
  qrcode_addr:string="";
  provider:any | null=null;
  private hAccessCode: any;
  access_code: any;
  message:string="";
  tab_title: string="Vos NFTs";
  opes: Operation[]=[];
  sel_ope:Operation | null=null;
  previews: any[]=[];
  owner: string="";
  attributes:string="";
  token_to_send: any=null;
  addr:string="";

  collections:Collection[]=[];

  image_for_token: string="";
  secret: string="";
  strong: boolean=false;

  sel_collection: string="*";
  options: any[]=[{label:"Toutes",value:"*"}];

  constructor(public routes:ActivatedRoute,
              public toast:MatSnackBar,
              public clipboard:Clipboard,
              public router:Router,
              public user:UserService,
              public socket:Socket,
              public _location:Location,
              public api:NetworkService) {
    this.version=environment.version;
  }


  generate_qrcode(){
    this.api.get_access_code(this.addr).subscribe((r:any)=>{
      this.url_key=r.image;
      this.access_code=r.access_code;
    });
  }


  ngOnInit(): void {
    getParams(this.routes).then((params:any)=>{
      $$("Récupération des paramètres: ",params);

      let network=params["network"] || "elrond-devnet";
      if(network=="db")network="db-server-nfluent";
      this.network=network;
      this.addr=params["addr"] || params["address"] || "";

      this.refresh_balance();
      this.showDetail=params["show_detail"] || false;

      this.generate_qrcode();
      this.hAccessCode=setInterval(()=>{this.generate_qrcode()},30000);

      this.socket.on("nfwallet_"+this.addr,(message:any)=>{
        if(message.action=="refresh")this.refresh(0);
        if(message.action.startsWith("http"))open(message.action+"?address="+this.addr);
      });
      this.refresh();
    },()=>{
      this.router.navigate(["pagenotfound"],{queryParams:{toolbar:false,message:"cette page ne correspond pas à un wallet connu"}});
    });
  }



  force_refresh(col:string | null=null){
    this.nfts=[];
    if(col)this.sel_collection=col;
    this.refresh(0);
  }



  add_nfts(r:NFT[],offset:number){
    for(let nft of r){
      if(this.sel_collection=="*"){
        this.nfts.push(nft);
      } else {
        if(nft.collection){
          if(nft.collection.id==this.sel_collection){
            this.message="";
            this.nfts.push(nft);
          }
        }
      }
      if(nft.collection){
        if(this.collections.map((x:Collection)=>{return x.id}).indexOf(nft.collection.id)==-1){
          let name=nft.collection.name ? nft.collection.name : nft.collection.id;
          this.collections.push(newCollection(name,nft.collection.owner,nft.collection.id));
          this.options.push({label:name,value:nft.collection.id}); //=this.collections.map((x:Collection)=>{return {label:x.name,value:x.id}})
        }
      }
    }

    if(this.nfts.length==0 && offset==0) {
      showMessage(this, "Vous n'avez aucun NFT pour l'instant")
      this.tab_title="Vos NFTs";
    } else {
      if (this.nfts.length > 1) {
        this.tab_title = "Vos " + r.length + " NFTs";
      } else {
        this.tab_title = "Votre NFT";
      }
    }
  }


  refresh(index:number=0) {
    $$("Refresh de l'onglet "+index);
    if(index!=2 && this.addr==""){
      showMessage(this,"Authentification requise");
      this.indexTab=2;
      return;
    }
    if(index==0 && this.nfts.length==0 && this.addr!=""){
      this.message=(this.sel_collection=="*") ? "Recherches de vos NFTs" : "Chargement de vos NFTs de la collection "+this.sel_collection;
      let offset=12;

      this.api.get_tokens_from("owner",this.addr,offset,true,null,0,this.network).then((r:any)=>{
        this.add_nfts(r.result,r.offset);
      },(err)=>{
        showError(this,err);
      });

      setTimeout(()=>{
        this.api.get_tokens_from("owner",this.addr,250,true,null,offset+1,this.network).then((r:any)=>{
          this.message="";
          this.add_nfts(r.result,r.offset);
        }).catch(err=>{showError(this,err)});
      },1500);
    }

    if(index==2){
      this.open_nftlive();
    }
  }


  public get triggerObservable(): Observable<void> {
    return this.trigger.asObservable();
  }


  public get nextWebcamObservable(): Observable<boolean|string> {
    return this.nextWebcam.asObservable();
  }


  //Envoi la photo pour fabrication de la collection
  showScanner: boolean=false;
  accescode_scan: string="";
  version: any;
  nft_size: number=350;
  balance: number=0
  claim="";
  appname="";
  visual="";

  handleImage(event: any) {
    let rc=event;
    if(!rc.startsWith('data:'))rc="data:image/jpeg;base64,"+rc;

    this.image_for_token=rc;
    this.message="Fabrication des modèles sur la base de l'image suivante";
    setTimeout(()=>{
      if(this.sel_ope && this.sel_ope.nftlive){
        this.api.send_photo_for_nftlive(
          this.sel_ope?.nftlive.limit,
          this.sel_ope?.nftlive?.nft_target.configuration,
          this.sel_ope.nftlive.nft_target.dimensions,
          this.sel_ope.nftlive.nft_target.quality,
          this.attributes,
          this.sel_ope.nftlive.dynamic_fields,
          {photo:rc}).subscribe((r:any)=>{
          this.message="";
          this.image_for_token="";
          this.photos_to_send=r.images.map((x:string)=>{return this.api.server_nfluent+"/api/images/"+x});
        },(err)=>{showError(this)});
      }
    },50);
  }


  photo() {
    this.trigger.next();
  }



  send(image:string) {
    if(this.sel_ope?.nftlive){
      let collection:Collection= {
        name: this.sel_ope?.nftlive!.nft_target.collection,
        id: "",
        roles:[],
        visual: undefined,
        description: undefined,
        owner: newCryptoKey(this.addr),
        price: undefined,
        type:"NFT",
        link:"",
        options:[]
      };

      let token:NFT= {
        attributes: [],
        tags: "",
        collection: collection,
        description: "description",
        miner: this.sel_ope.nftlive.nft_target.miner,
        files: [],
        supply: 1,
        price: 0,
        type: "NonFungibleESDT",
        balances:{},
        message: undefined,
        name: this.sel_ope?.nftlive!.nft_target.name,
        network: this.network,
        owner: this.addr,
        royalties: this.sel_ope.nftlive.nft_target.royalties,
        visual: image,
        symbol: '',
        creators: [],
        address: undefined,
        solana: undefined,
        style: undefined,
        links: undefined
      }


      if(token.miner){

        if(!this.owner)this.owner=this.addr;

        this.message="Minage en cours";
        this.api.mint(token,token.miner,this.owner,this.sel_ope.id,false,"nftstorage",this.network).then((r:any)=>{
          this.message="";
          showMessage(this,"Votre NFT est miné et envoyé. Vous pouvez en miner un autre");
          this.token_to_send=null;
        })
      }
    }
  }


  ngOnDestroy(): void {
    clearInterval(this.hAccessCode);
  }



  show_elrond_addr() {
    showMessage(this,"Votre adresse est disponible dans le presse-papier");
    this.clipboard.copy(this.addr);
    this.api.qrcode(this.addr,"json").subscribe((result:any)=>{
      this.qrcode_addr=result.qrcode;
    })

  }


  open_nftlive() {
    this.api.nftlive_access(this.addr,this.network).subscribe((r:any)=>{
      this.opes=r;
      if(r.length==1)this.sel_ope=r[0];
    })
  }

  on_upload($event: any) {
    this.handleImage($event.file)
  }

  reset() {
    this.photos_to_send=[];
  }

  get_opacity(img: string) {
    if(!this.token_to_send)return 1;
    if(img==this.token_to_send)return 1;
    return 0.4;
  }

  update_identity_photo($event: any) {
    this.secret=$event.file;
  }

  save_privacy() {
    this.api.save_privacy(this.addr,this.secret).subscribe(()=>{
      this.strong=false;
    })
  }

  refresh_balance(){
    if(this.addr!="")this.api.getBalance(this.addr,this.network).subscribe((res)=>{
      this.balance=res[0].balance/1e18
    });
  }

  on_authent($event: any) {
    //Cette fonction est déclenché dans le cadre du nfluent_wallet_connect
    this.strong=$event.strong;
    if(this.addr.length>0 && this.addr!=$event.address){
      showMessage(this,"Cette identification ne correspond pas au wallet ouvert");
      this.strong=false;
      return;
    }
    if($event.strong){
      this.addr=$event.address;
      this.refresh_balance();
      showMessage(this,"Vous êtes maintenant pleinement connecté à votre wallet");
      setTimeout(()=>{this.indexTab=0;},1500);
    }
  }

  on_disconnect(){
    showMessage(this,"Déconnexion");
    this.strong=false;
  }

  on_scan($event: any) {
    //Déclenché par le scanner en mode nfluent wallet connect
    this.showScanner=false;
    $$("Analyse de "+$event.data);
    this.api.scan_for_access($event.data,this.addr).subscribe((result:any)=>{
      showMessage(this,"Vérification de détention des NFT")
    },(err:any)=>{
      showError(this,err);
    });
  }

  isProd() {
    return !isLocal(environment.appli)
  }

  paste_code(evt:ClipboardEvent) {
    if(evt.clipboardData){
      this.on_scan({data:evt.clipboardData.getData("text")});
    }

  }

  open_inspire() {
    open(this.api.getExplorer(this.addr),"Explorer");
  }

  open_gallery() {
    open(environment.appli+"/gallery?"+setParams({
      toolbar:false,address:this.addr,canChange:false,duration:10,background:"https://nfluent.io/assets/paper3.jpg"
    }),"gallery")

  }


  on_reverse(evt:any) {

  }

  on_rescue($event: any) {
    showMessage(this,$event);
  }

  analyse_metadata(nft: NFT) {
    let index=this.nfts.indexOf(nft)
    if(nft.attributes.length==1 && nft.attributes[0].value.indexOf("metadata:")>-1 && nft.address){
      this.api.get_nft(nft.address,this.network,this.addr).subscribe((result:any)=>{
        if(result.length>0){
          nft=result[0]
          for(let i=0;i<nft.attributes.length;i++){
            let a=nft.attributes[i];
            if(a.trait_type=="lazymint")nft.attributes.splice(i,1);
          }
          this.nfts[index]=nft;
        }
      })
    }
  }

  logout() {
    this.addr="";
    this._location.go("/wallet",setParams({toolbar:false}))
  }
}
