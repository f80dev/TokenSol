import {Component, Input, OnDestroy, OnInit} from '@angular/core';
import {NetworkService} from "../network.service";
import {$$, getParams, isLocal, showError, showMessage} from "../../tools";
import {ActivatedRoute, Router} from "@angular/router";
import {environment} from "../../environments/environment";
import {MatSnackBar} from "@angular/material/snack-bar";
import {Observable, Subject} from "rxjs";
import {WalletConnectProvider} from '@elrondnetwork/erdjs-wallet-connect-provider';
import {Location} from "@angular/common";
import {NFT} from "../../nft";
import {Collection, Operation} from "../../operation";
import {UserService} from "../user.service";
import {Clipboard} from "@angular/cdk/clipboard";

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
  qrcode_addr:string="";
  provider:WalletConnectProvider | null=null;
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

  collections:Collection[]=[{
    description: undefined,
    id: "*",
    type:"NFT",
    owner: undefined,
    price: undefined,
    link:"",
    visual: undefined,
    name:"Toutes",
    roles: [],
    options: {
      canAddSpecialRoles: true,
      canChangeOwner: true,
      canFreeze: true,
      canPause: true,
      canWipe: true,
      canUpgrade: true,
      canTransferNFTCreateRole: true
    }

  }];

  sel_collection: Collection=this.collections[0];
  image_for_token: string="";
  secret: string="";
  strong: boolean=false;


  constructor(public routes:ActivatedRoute,
              public toast:MatSnackBar,
              public clipboard:Clipboard,
              public router:Router,
              public user:UserService,
              public _location:Location,
              public network:NetworkService) {
    this.version=environment.version;
  }


  generate_qrcode(){
    this.network.get_access_code(this.addr).subscribe((r:any)=>{
      this.url_key=r.image;
      this.access_code=r.access_code;
    });
  }

  ngOnInit(): void {
    getParams(this.routes,"wallet_params").then((params:any)=>{
      $$("Récupération des paramètres: ",params);
      this.addr=params["addr"];
      if(!this.addr)this.addr=this.user.addr;
      if(!this.addr)showMessage(this,"Adresse non disponible, vous pouvez fermer cette fenêtre");
      this.showDetail=params["show_detail"] || false;
      this.network.network=params["network"] || "elrond-mainnet";
      this.generate_qrcode();
      this.hAccessCode=setInterval(()=>{this.generate_qrcode()},30000);
      this.refresh();
    },()=>{
      this.router.navigate(["pagenotfound"],{queryParams:{toolbar:false,message:"cette page ne correspond pas à un wallet connu"}});
    });
  }


  force_refresh(){
    this.nfts=[];
    this.refresh(0);
  }


  add_nfts(r:NFT[],offset:number){
    for(let nft of r){
      let col=nft.collection;
      if(this.sel_collection.id=="*"){
        this.nfts.push(nft);
      } else {
        if(nft.collection){
          if(nft.collection.id==this.sel_collection.id){
            this.message="";
            this.nfts.push(nft);
          }
        }
      }
      if(nft.collection){
        if(this.collections.map((x:Collection)=>{return x.id}).indexOf(nft.collection["id"])==-1)this.collections.push(nft.collection);
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
    if(index==0 && this.nfts.length==0){
      this.message="Chargement NFTs";
      this.network.get_tokens_from("owner",this.addr,5,true,null,0,this.network.network).then((r:any)=>{
        this.add_nfts(r.result,r.offset);
      });

      setTimeout(()=>{
        this.network.get_tokens_from("owner",this.addr,250,true,null,5,this.network.network).then((r:any)=>{
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
  nft_size: number | null=250;

  handleImage(event: any) {
    let rc=event;
    if(!rc.startsWith('data:'))rc="data:image/jpeg;base64,"+rc;

    this.image_for_token=rc;
    this.message="Fabrication des modèles sur la base de l'image suivante";
    setTimeout(()=>{
      if(this.sel_ope && this.sel_ope.nftlive){
        this.network.send_photo_for_nftlive(
          this.sel_ope?.nftlive.limit,
          this.sel_ope?.nftlive?.nft_target.configuration,
          this.sel_ope.nftlive.nft_target.dimensions,
          this.sel_ope.nftlive.nft_target.quality,
          this.attributes,
          this.sel_ope.nftlive.dynamic_fields,
          {photo:rc}).subscribe((r:any)=>{
          this.message="";
          this.image_for_token="";
          this.photos_to_send=r.images.map((x:string)=>{return this.network.server_nfluent+"/api/images/"+x});
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
        owner: undefined,
        price: undefined,
        type:"NFT",
        link:"",
        options:{
          canWipe:true,
          canTransferNFTCreateRole:true,
          canUpgrade:true,
          canPause:true,
          canFreeze:true,
          canChangeOwner:true,
          canAddSpecialRoles:true
        }
      };

      let token:NFT= {
        attributes: [],
        tags:"",
        collection: collection,
        description: "description",
        files: [],
        marketplace: {quantity: 1, price: 0},
        message: undefined,
        name: this.sel_ope?.nftlive!.nft_target.name,
        network: this.network.network,
        owner: this.addr,
        royalties: this.sel_ope.nftlive.nft_target.royalties,
        visual: image,
        symbol: '',
        creators: [],
        address: undefined,
        solana: undefined,
        style: undefined
      }

      if(this.sel_ope?.nftlive?.nft_target.miner){

        if(!this.owner)this.owner=this.addr;

        this.message="Minage en cours";
        this.network.mint(token,this.sel_ope?.nftlive?.nft_target.miner,this.owner,this.sel_ope.id,false,"nftstorage",this.network.network).then((r:any)=>{
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
    this.network.qrcode(this.addr,"json").subscribe((result:any)=>{
      this.qrcode_addr=result.qrcode;
    })

  }


  open_nftlive() {
    this.network.nftlive_access(this.addr,this.network.network).subscribe((r:any)=>{
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
    this.network.save_privacy(this.addr,this.secret).subscribe(()=>{
      this.strong=false;
    })
  }

  on_authent($event: any) {
    //Cette fonction est déclenché dans le cadre du nfluent_wallet_connect
    this.strong=$event.strong;
    if($event.strong){
      if(this.addr=="")this.addr=$event.address;
      if(this.addr==$event.address){
        showMessage(this,"Vous êtes maintenant pleinement connecté à votre wallet");
      }else{
        showMessage(this,"Ce wallet ne correspond pas à votre wallet actuelle");
        this.strong=false;
      }
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
    this.network.scan_for_access($event.data,this.addr).subscribe((result:any)=>{
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
    this.network.open_gallery(this.addr);
  }


  on_reverse(evt:any) {
    if(typeof(evt.data)=="string")evt.data=JSON.parse(evt.data);
    if(evt.side && evt.data.description.length==0 && (!evt.data.attributes || evt.data.attributes.length==0)){
      this.network.get_nft(evt.data.address,this.network.network).subscribe((result:any)=>{
        let index=this.nfts.indexOf(evt.data);
        this.nfts[index]=result[0];
        for(let i=0;i<this.nfts[index].attributes.length;i++){
          let a=this.nfts[index].attributes[i];
          if(a.trait_type=="lazymint")this.nfts[index].attributes.splice(i,1);
        }
     })
    }
  }
}
