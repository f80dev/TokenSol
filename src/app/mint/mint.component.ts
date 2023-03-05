import {Component, OnInit} from '@angular/core';
import {
  $$, b64DecodeUnicode,
  base64ToArrayBuffer, copyAchievements, find,
  getParams, newCryptoKey, now,
  showError,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {MAX_FILE_SIZE} from "../../definitions";
import {NetworkService} from "../network.service";

import ExifReader from 'exifreader';
import {UserService} from "../user.service";
import {ActivatedRoute, Router} from "@angular/router";

import {OperationService} from "../operation.service";
import {NFT} from "../../nft";
import {Clipboard} from "@angular/cdk/clipboard";
import {Location} from "@angular/common";
import {Collection, newCollection, Operation} from "../../operation";
import {environment} from "../../environments/environment";


@Component({
  selector: 'app-mint',
  templateUrl: './mint.component.html',
  styleUrls: ['./mint.component.css']
})
export class MintComponent implements OnInit {

  fileName: string="";
  key: string="";
  formData: FormData=new FormData();
  sign: boolean=false;
  tokens: NFT[]=[];
  sel_platform: any;
  sel_platform_document: any;
  price: any=0;
  quantity: any=1;
  sel_collection:Collection | undefined;
  mintfile: string="sf_"+now()+".yaml";
  sel_network:{label:string,value:string} | undefined;
  networks:any[]=[];

  //Opére le minage.
  //Cette fonction est à la fois utilisé par le process récurent en masse et le process individuel
  create_options: any=[
    {label:"Create",value:"ESDTRoleNFTCreate"},
    {label:"Burn",value:"ESDTRoleNFTBurn"},
    {label:"Update",value:"ESDTRoleNFTUpdateAttributes"},
    {label:"Add URI",value:"ESDTRoleNFTAddURI"},
    {label:"TransferRole",value:"ESDTTransferRole"}
  ]
  //sel_target: {value:string,label:string}={value:"",label:""};
  targets=[
    {label:"blockchain",value:"blockchain",only_advanced:false},
    {label:"base de données",value:"db-server-nfluent",only_advanced:false},
    {label:"base décentralisée",value:"db-web3-nfluent",only_advanced:true},
    {label:"serveur",value:"vile",only_advanced: true},
    {label:"Prestashop",value:"prestashop",only_advanced:true},
  ];

  sel_target: { value:string,label:string }=this.targets[0];
  encrypt_nft: boolean = true;
  sel_addr: string="";
  message: string="";
  collection_name: string = "";

  constructor(
      public toast:MatSnackBar,
      public network:NetworkService,
      public dialog:MatDialog,
      public user:UserService,
      public operation:OperationService,
      public _location:Location,
      public router:Router,
      public clipboard:Clipboard,
      public routes:ActivatedRoute,
  ) {
    //this.user.addr_change.subscribe((addr)=>{this.init_form();})
    this.sel_platform=this.network.config["PLATFORMS"][0];              //NFTStorage
    this.sel_platform_document=this.network.config["PLATFORMS"][3];     //Server
  }


  ngOnInit(): void {
    this.init_form();
  }


  init_form(){
    let tmp=localStorage.getItem("tokenstoimport");
    let local_config=JSON.parse(localStorage.getItem("miner_config") || "{}")

    this.targets=this.targets.filter((x)=>{return(this.user.advance_mode || !x.only_advanced)})

    this.sel_target=local_config.target || this.targets[0];
    if(tmp)this.tokens=JSON.parse(tmp);

    if (this.user.nfts_to_mint.length > 0) {
      $$("Chargement des NFT depuis la fenetre de création");
      this.onFileSelected(this.user.nfts_to_mint);
      this.user.nfts_to_mint=[];
    }

    getParams(this.routes).then((params:any)=> {

      if(params.import){this.batch_import_from_url(params.import);}
      let l_nets=params.networks ? params.networks.split(",") : this.network.config["NETWORKS"]; //Chargement des réseaux autorisé en priorité via les parametres
      this.networks=l_nets.map((x:any)=>{return {label:x,value:x}});
      this.sel_network=local_config.network || this.networks[0];


      //Récupération d'une collection en particulier
      if (params.hasOwnProperty("collection")) {
        if (this.user.find_collection(params["collection"])) {
          this.sel_collection = params["collection"];
        } else {
          this.sel_collection = local_config.collection || this.user.collections[0];
        }
      }

      if (params.hasOwnProperty("files")) {
        let files = [];
        for (let f of params["files"]) {
          files.push({filename: f});
        }
        this.onFileSelected(files);
      }
    })
  }



  get_token_from_xmp(_infos:any,url:string):NFT {
    let creators:any[]=[];
    if(_infos.creators && _infos.creators.length>0){
      for(let line of _infos.creators.split("\n")){
        if(line && line.indexOf("=")>-1){
          let addr=line.split("=")[0].trim();
          let share=Number(line.split("=")[1].trim().replace("%",""));
          creators.push({address:addr,share:share,verified:0})
        }
      }
    } else {
      if(this.user.key){
        creators.push(
            {
              address: this.user.key?.address!,
              share:100,
              verified: 0
            }
        )
      }
    }

    let attributes:any[]=[];

    if(_infos.hasOwnProperty("properties")){
      for(let a of _infos.properties.split("\n")){
        if(a.length>1){
          if(a.indexOf("=")>-1){
            attributes.push({trait_type:a.split("=")[0].trim(),value:a.split("=")[1].trim()})
          } else {
            attributes.push({trait_type:"",value:a})
          }
        }
      }
    }

    if(!_infos.hasOwnProperty("files") || _infos.files=="")_infos["files"]=[];

    let marketplace={price:this.price,quantity:this.quantity};
    if(_infos.hasOwnProperty("marketplace"))marketplace=_infos.marketplace;

    let rc:NFT={
      collection: null,
      address: undefined,
      message:"",
      tags:_infos.tags,
      attributes: attributes,
      creators: creators,
      description: _infos.description,
      symbol: _infos.symbol,
      files: _infos.files,
      marketplace: marketplace,
      name: _infos.title,
      network: this.network.network,
      miner:newCryptoKey(""),
      owner: this.user.addr,
      royalties: !_infos.royalties ? 0 : _infos.royalties,
      visual: url,
      solana:null,
      style:{}
    }

    return(rc);
  }



  onCollectionSelected(file:any){
    this.network.extract_zip(file).subscribe((images:any)=>{
      this.tokens=images;
    });
  }



  onFileSelected(files: any) {
    //tag: upload_file
    //Import/Upload des NFT: chargement depuis un fichier ou la fenetre
    if(files.hasOwnProperty("filename"))files=[files]
    let index=0;
    for(let f of files) {
      if(f.filename.startsWith("http")){
        fetch(f.filename).then((resp) => {
          resp.arrayBuffer().then((data)=>{
            //this.tokens.push();
          })
        })
      }

      if(f.filename.endsWith(".json")){
        const fr = new FileReader();
        fr.onload = () => {
          let fileContent = fr.result;
          if(typeof fileContent==="string"){
            let content=JSON.parse(fileContent);
            $$("Ajout de "+content.name);
            this.tokens.push(content);
            this.local_save();
          }
        }
        fr.readAsText(f);
      } else {
        let tags: any={}
        let content=f.hasOwnProperty("file") ? f.file : f.src;
        try {
          tags = ExifReader.load(base64ToArrayBuffer(content.split("base64,")[1]))
        } catch (e) {}

        let url=content;
        let _infos:any={};
        if(tags.hasOwnProperty("mint")){
          const s_tmp=b64DecodeUnicode(tags.mint.value)
          _infos= JSON.parse(s_tmp);
        }
        if(_infos.hasOwnProperty("storage")){
          url=_infos["storage"];
          if(!url.startsWith("http"))url=environment.server+url;
        }
        this.tokens.push(this.get_token_from_xmp(_infos,url))
      }
    }
    this.local_save();
  }


  confirm_mint(){
    let nbtokens=this.tokens.length;
    _prompt(this,
        "Confirmer le minage","",
        "html:... de "+nbtokens+" NFTs sur le réseau "+this.network.network+"<br>par le compte <strong>"+this.user.key?.name+"</strong> dans la collection "+this.sel_collection?.name +" ?",
        "","Ok","Annuler",true
    ).then((rep)=>{
      if(rep=="yes"){
        showMessage(this,"Lancement du processus de minage");
        this.mintfile="sf_"+now()+".yaml";
        this.message="Production du fichier";
        this.content_for_clipboard="";
        this.mint(0);
      }
    });
  }


  //Fonction récurente appeler pour le minage en masse
  content_for_clipboard: string="";

  mint(index=0){
    if(index>=this.tokens.length){
      showMessage(this,"Traitement terminé");
    } else {
      let _t:NFT=this.tokens[index];
      _t.marketplace={price:this.price,quantity:this.quantity}
      _t.message="hourglass:Minage";

      this.miner(_t).then((nft:any)=>{
        this.content_for_clipboard=this.content_for_clipboard+"\t\t\t\t- "+nft.message+"\n"
        if(this.sel_target.value=="file"){
          nft.message="miné";
          nft.address="";
        }
        this.local_save();
        this.mint(index+1);
      }).catch((result:any)=>{
        _t.message="Anomalie de minage: "+result.message;
      });
    }
  }


  clear() {
    _prompt(this,"Effacer les NFT a miner","","Etes-vous sûr de vouloir tout effacer ?","","Effacer tout","Annuler",true).then(()=>{
      $$("Effactement des tokens")
      this.tokens=[];
      this.local_save();
    })
  }



  local_save(){
    localStorage.setItem("tokenstoimport",JSON.stringify(this.tokens));
    localStorage.setItem("miner_config",JSON.stringify({
      target:this.sel_target,
      network:this.sel_network,
      miner:this.sel_addr,
      platform:this.sel_platform,
      document_platform:this.sel_platform_document,
      collection:this.sel_collection
    }))
  }


  upload_file(file:any){
    return new Promise((resolve, reject) => {
      file.type="image/webp";
      this.network.upload(file,this.sel_platform.value,file.type).subscribe((r: any) => {
        localStorage.removeItem("attach_file_" + file.uri);
        resolve(r.url)
        showMessage(this, "upload ok");
        this.local_save();
      },(err) => {
        showError(err);
        reject(err);
      })
    });
  }


  upload_token(token: NFT) {
    for(let file of token.files){
      this.upload_file(file).then((r:any)=>{
        file.uri=r;
      })
    }
    token.message="visual uploading ...";
    this.message="Upload du visuel";
    this.upload_file({content:token.visual,type:""}).then((r:any)=>{
      token.visual=r;
      token.message="visual uploaded";
      this.local_save();
    }).finally(()=>{this.message="";});

  }


  upload_all_tokens() {
    for(let i=0;i<this.tokens.length;i++){
      setTimeout(()=>{
        this.message="Upload de "+i+"/"+this.tokens.length+" en cours";
        this.upload_token(this.tokens[i]);
        if(i==this.tokens.length-1){
          this.local_save();
          this.message="";
        }
      },i*2000);
    }
  }







  miner(token: NFT) : Promise<any> {
    return new Promise<any>((resolve, reject) => {
      if(this.user.key==undefined){
        reject("no signature");
      }

      //if(!token.collection)token.collection=this.sel_collection || null;
      if(this.network.isElrond()){
        token.collection=this.user.find_collection(this.sel_collection?.id);
      }else{
        token.collection=newCollection(this.collection_name)
      }

      if(this.isValide(token)==""){
        token.message="Minage en cours";
        if(this.sel_target.value=="prestashop"){
          this.prestashop(token).subscribe((result:any)=>{
            showMessage(this,"NFT ajouter à prestashop");
            result.nft=token
            resolve(result);
          });
        }

        let error_message="";

        if(!this.user.key)error_message="Vous devez avoir sélectionné une clé";
        if(error_message.length>0){
          showMessage(this,error_message);
          reject(error_message);
          token.message="Error: "+error_message;
        }

        if(this.user.key){
          let id_operation=this.operation.sel_ope ? this.operation.sel_ope.id : "";
          let target_network=this.sel_target.value;

          token.owner=this.user.addr;

          if(target_network=="blockchain"){
            target_network=this.network.network;
            token.network=target_network;
          }
          this.message="Minage du NFT "+token.name;
          this.network.mint(token,this.user.key,token.owner || "",id_operation,this.sign, this.sel_platform.value,target_network,this.mintfile,this.encrypt_nft).then((result:any)=>{
            this.message="";
            if(!result.error || result.error==""){
              token.address=result.result.mint;
              if(target_network=="file"){
                if(this.encrypt_nft)result.out="encrypt: \""+result.out+"\"";
                this.clipboard.beginCopy(result.out).copy();
                token.message=result.out;
              } else {
                token.message="NFT id="+token.address+", minted for 0"
              }
              resolve(token);
            } else {
              token.message=result.error;
              reject(result.error);
            }
          }).catch((err)=>{
            this.message="";
            token.message=err.error;
            showError(err);
          })
        }
      } else {
        reject(token);
        showMessage(this,"Minage impossible: "+this.isValide(token));
      }
    });
  }


  find_name(creator: any): string {
    for(let k of this.network.keys)if(k.address==creator.address)return(k.name);
    return creator.address;
  }


  see_in_hub(nft:NFT){
    if(!nft.address)return;
    if(nft.address.startsWith('db_')){
      showMessage(this,nft.address)
    } else {
      this.network.open_gallery(nft.address);
    }
  }


  download_all(){
    if(this.tokens.length>0){
      this.network.archive(this.tokens).then((r:any)=>{
        if(r)open(r,"_blank");
      })
    }
  }

  add_miner_to_creator(){
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
          {
            title: "Royalties pour "+this.user.key?.name,
            type: "number",
            onlyConfirm:false,
            lbl_ok:"Ok",
            lbl_cancel:"Annuler"
          }
    }).afterClosed().subscribe((royalties) => {
      if(royalties){
        for(let t of this.tokens){
          if(t.creators.length>0){
            t.creators[0].share=t.creators[0].share-Number(royalties);
            t.creators.push({
              verified: 0,
              address:this.user.key?.address,
              share:Number(royalties)
            });
          } else {
            t.creators.push({
              verified: 0,
              address:this.user.key?.address,
              share:100
            });
          }

        }
        this.local_save();
      }
    });

  }

  add_creator() {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
          {
            title: "Adresse du créateur ?",
            type: "text",
            result:this.user.key?.address,
            onlyConfirm:false,
            lbl_ok:"Ok",
            lbl_cancel:"Annuler"
          }
    }).afterClosed().subscribe((new_addr:string) => {
          if (new_addr){
            for(let t of this.tokens){
              t.creators.push({
                verified: 0,
                address:new_addr,
                share:0
              });
            }
            this.local_save();
          }
        }
    );
  }

  remove(token: any) {
    let idx=this.tokens.indexOf(token);
    this.tokens.splice(idx,1);
    this.local_save();
  }



  isValide(token: any):string {
    $$("Vérifier la validiter du token pour le minage");
    if(token.properties){
      for(let f of token.properties.files){
        if(!f.uri.startsWith("http"))return("Au moins un des fichier attaché n'est pas partagé");
      }
      if(!token.image.startsWith("http"))return "Le visuel n'est pas partagé";
      let canSign=false;
      for(let c of token.properties.creators){
        if(c.address==this.user.key?.address)canSign=true;
      }
      if(!canSign)return "Le miner ne fait pas parti des créateurs";
    }
    if(token.visual=="")return "Le NFT doit avoir un visuel";
    if(!token.visual.startsWith("https"))return "Le visuel n'est pas en ligne";
    if(!token.collection)return "Le token doit être rataché à une collection";
    return "";      //Le token est valide
  }







  onUploadXMP(file: any, token: NFT) {
    let pos=this.tokens.indexOf(token);
    let xmp_data=atob(file.file.split("base64,")[1]).split("mint=")[1]
    xmp_data=xmp_data.substring(1).split("'")[0]
    let _infos=JSON.parse(atob(xmp_data))
    token=this.get_token_from_xmp(_infos,token.visual);
    this.tokens[pos]=token;
  }


  prestashop(token:NFT) {
    return this.network.export_to_prestashop(this.operation.sel_ope!.id,[token],false);
  }

  set_network() {
    for(let nft of this.tokens)
      nft.network=this.network.network;
    showMessage(this,"Changement terminé")
  }

  reset_creator() {
    for(let t of this.tokens){
      t.creators=[{
        verified: 0,
        address:this.user.key?.address,
        share:100
      }];
    }
  }

  set_marketplace(token: NFT) {
    if(token){
      token.marketplace={price:this.price,quantity:this.quantity};
    }
  }

  edit_attribute(a: { trait_type: string; value: string }) {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
          {
            title: "modifier le trait_type et/ou la valeur",
            result: a.trait_type+":"+a.value,
            onlyConfirm: false,
            lbl_ok:"Ok",
            lbl_cancel:"Annuler"
          }
    }).afterClosed().subscribe((rep:string) => {
      if(rep){
        a.trait_type=rep.split(":")[0];
        a.value=rep.split(":")[1];
      }
    });
  }

  clone_attribute() {
    for(let i=1;i<this.tokens.length;i++){
      this.tokens[i].attributes=this.tokens[0].attributes;
    }
    showMessage(this,"Recopie terminée")
  }

  clone_name() {
    for(let i=1;i<this.tokens.length;i++){
      this.tokens[i].name=this.tokens[0].name;
      this.tokens[i].description=this.tokens[0].description;
    }
    showMessage(this,"Recopie terminée")
  }

  add_attribute() {
    this.tokens[0].attributes.push({trait_type: "nom de l'attribut", value: "valuer de l'attribut"})
    this.edit_attribute(this.tokens[0].attributes[this.tokens[0].attributes.length-1]);
  }

  open_collections() {
    this.router.navigate(["collections"],{queryParams:{owner:this.user.addr}});
  }

  clear_attribute() {
    this.tokens[0].attributes=[];
  }

  clone_marketplace() {
    for(let i=1;i<this.tokens.length;i++){
      this.tokens[i].marketplace=this.tokens[0].marketplace;
      this.tokens[i].royalties=this.tokens[0].royalties;
    }
    showMessage(this,"Recopie terminée")
  }

  batch_import_from_url(url:string) {
    this.network.upload_batch({content:url}).subscribe((rows:NFT[])=>{
      this.tokens=rows;
      showMessage(this,"Fichier importé");
    })
  }

  batch_import(files: any) {
    if (files.hasOwnProperty("filename")) files = [files]
    let index = 0;
    for (let f of files) {
      if (f.filename.endsWith("xlsx")) {
        this.network.upload_batch({content:f.file}).subscribe((rows:NFT[])=>{
          this.tokens=rows;
          showMessage(this,"Fichier importé");
        })
      }
    }
  }

  drop(files: File[],token:NFT) {
    //Intégration des fichiers attachés
    if(this.sel_platform_document.value!="nftstorage"){
      this.message="Décodage des fichiers";
      for(let file of files){
        if(file.size>MAX_FILE_SIZE*1024){
          this.message="";
          showMessage(this,"La taille de "+file.name+" excéde la limite de "+MAX_FILE_SIZE+" ko. Vous pouvez le mettre en ligne et coller le lien dans cette zone",10000)
        } else {
          let reader = new FileReader();
          reader.onload=()=>{
            let body={filename:file.name,content:reader.result,type:file.type};
            this.message="Mise en ligne du document";
            this.network.upload(body,this.sel_platform_document.value,file.type).subscribe((r:any)=>{
              this.message="";
              token.files.push(r.url);
              this.local_save();
            });

          }
          reader.readAsDataURL(file)
        }
      }
    } else {
      showMessage(this,"Impossible de mettre en ligne des documents attachés sur la plateforme "+this.sel_platform.label);
    }
  }

  open_link(token: NFT, file: any) {
    open(file,"view_document")
  }

  delete_link(token: NFT, file: any) {
    let idx=token.files.indexOf(file);
    token.files.splice(idx,1);
  }



  sync_on_ope() {
    if(this.operation.sel_ope) {
      let ope: Operation = this.operation.sel_ope;
      _prompt(this, "Utiliser les paramétres de l'opération", "", ope?.title, "text", "Oui", "Non", true).then((r) => {
        if (r) {
          let _n: any = ope.lazy_mining?.networks[0];
          if (_n) {
            this.network.network_change.subscribe(() => {
              this.user.init(_n.miner,this.network.network).then(()=>{
                let index=find(this.user.collections,_n.collection,"id");
                if(index>-1)this.sel_collection = this.user.collections[index];
              })
            })
            this.network.network = _n.network;

            for(let src of ope.data.sources){
              if(src.type=="database"){
                let index=find(this.targets,{value:src.connexion,label:src.connexion},"value");
                if(index>-1)this.sel_target=this.targets[index];
              }
            }
          } else {
            this.sel_target=this.targets[0];
            this.network.network=ope.network;
          }
        }
      })
    }
  }

  show_transaction(token: NFT) {

  }

  informe_copy_collection() {
    showMessage(this,"La collection est copié. Vous pouvez l'insérer dans le fichier d'opération")
  }

  confirm_clipboard() {
    showMessage(this,"Opération effectuée. Vous pouvez insérer les NFT dans un fichier d'opération");
  }

  nfts_to_clipboard() : string {
    let rc="nfts:\n";
    for(let nft of this.tokens) {
      rc = rc + "\t- " + nft.visual + "\n"
    }
    return rc;
  }

  clear_content_for_clipboard($event: KeyboardEvent) {
    if($event.ctrlKey && ($event.key=="c" || $event.key=='C' || $event.key=="x" || $event.key=='X')){
      showMessage(this,"Les NFT sont disponibles dans le presse papier. Vous pouvez les ajouter dans un fichier d'opération")
      setTimeout(()=>{
        this.content_for_clipboard="";
      },1000);
    }
  }

  open_document(file: any) {
    open(file.split("filename=")[0],"_blank");
  }

  updateChain($event:any) {
    this.network.network=$event.value;
    // this.network.init_keys($event.value);
  }

  updateUser($event: any) {
    this.sel_addr=$event;
    let with_collection=this.network.isElrond();
    this.user.init($event,this.network.network,with_collection);
  }

  changeCollection($event: any) {
    this.sel_collection=$event
  }

  show_file(filename: string) : string {
    if(filename.indexOf("f=")>-1)return(atob(filename.split("f=")[1]));
    if(filename.indexOf("filename=")>-1)return(filename.split("filename=")[1]);
    let pos=filename.lastIndexOf("/");
    return filename.substring(pos+1);
  }
}
