import {Component, OnInit} from '@angular/core';
import {
  $$, b64DecodeUnicode,
  base64ToArrayBuffer, CryptoKey, exportToCsv, find,
  getParams, isEmail, newCryptoKey, now,
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
import {Creator, NFT} from "../../nft";
import {Clipboard} from "@angular/cdk/clipboard";
import {Location} from "@angular/common";
import {Collection, newCollection, Operation} from "../../operation";
import {environment} from "../../environments/environment";
import {wait_message} from "../hourglass/hourglass.component";
import {_ask_for_paiement} from "../ask-for-payment/ask-for-payment.component";



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
  networks:any[]=[];
  token_creators: Creator[]=[];

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
  // targets=[
  //   {label:"blockchain",value:"blockchain",only_advanced:false},
  //   {label:"base de données",value:"db-server-nfluent",only_advanced:false},
  //   {label:"base décentralisée",value:"db-web3-nfluent",only_advanced:true},
  //   {label:"serveur",value:"vile",only_advanced: true},
  //   {label:"Prestashop",value:"prestashop",only_advanced:true},
  // ];

  //sel_target: { value:string,label:string }=this.targets[0];
  encrypt_nft: boolean = true;
  sel_key: CryptoKey | undefined;
  message: string="";
  collection_name: string = "";
  show_mint_section: boolean=false;
  collections: Collection[]=[]

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
    // this.user.addr_change.subscribe((addr)=>{
    //   if(this.user.collections.length>0)this.sel_collection=this.user.collections[0];
    // })

  }


  ngOnInit(): void {
    setTimeout(()=>{
      this.init_form();
    },2500)
  }

  set_creators(){
    for(let t of this.tokens){
      if(!t.address)t.creators=this.token_creators;
    }
  }

  async init_form(){
    let tmp=localStorage.getItem("tokenstoimport");

    let local_config=JSON.parse(localStorage.getItem("miner_config") || "{}")
    this.token_creators=local_config.creators || [];

    this.networks=this.network.networks_available.map((x:any)=>{return {label:x,value:x}});
    let keys=await this.network.init_network(local_config.network || this.networks[0].value);
    if(!keys){
      showError(this,"Impossible de récupérer les clés");
      keys=[]
    }
    if(keys.length>0){
      this.update_miner(local_config.key ? this.network.find_key_by_address(local_config.key.address) : keys[0])
    }

    this.sel_platform=this.network.config["PLATFORMS"][0];              //NFTStorage
    this.sel_platform_document=this.network.config["PLATFORMS"][3];     //Server

    if(tmp){
      this.tokens=JSON.parse(tmp);
      this.set_creators();
    }

    if (this.user.nfts_to_mint.length > 0) {
      $$("Chargement des NFT depuis la fenetre de création");
      this.onFileSelected(this.user.nfts_to_mint);
      this.user.nfts_to_mint=[];
    }


    let params:any=await getParams(this.routes);
    if(params.import){this.batch_import_from_url(params.import);}

    //Récupération d'une collection en particulier

    // if (params.hasOwnProperty("collection")) {
    //   if (this.user.find_collection(params["collection"])) {
    //     this.sel_collection = params["collection"];
    //   } else {
    //     setTimeout(()=>{
    //       this.sel_collection = local_config.collection || this.user.collections[0];
    //     },1000)
    //   }
    // }

    if (params.hasOwnProperty("files")) {
      let files = [];
      for (let f of params["files"]) {
        files.push({filename: f});
      }
      this.onFileSelected(files);
    }
  }


  get_token_from_xmp(_infos:any,visual:string):NFT {
    //Analyse les infos et le visuel pour créer le NFT
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
      if(this.sel_key){
        creators.push(
            {
              address: this.sel_key?.address!,
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

    if(!_infos.hasOwnProperty("files") || _infos.files=="")
      _infos["files"]=[];
    else
      _infos["files"]=_infos["files"].split("\n");

    let rc:NFT={
      collection: undefined,
      address: undefined,
      message:"",
      tags:_infos.tags,
      attributes: attributes,
      creators: creators,
      description: _infos.description,
      symbol: _infos.symbol,
      balances:{},
      type: "NonFungibleESDT",
      files: _infos.files,
      supply: _infos.supply,
      price: _infos.price,
      name: _infos.title,
      network: this.network.network,
      miner:newCryptoKey(""),
      owner: this.user.addr,
      royalties: !_infos.royalties ? 0 : _infos.royalties,
      visual: visual,
      solana:null,
      style:{},
      links:undefined
    }


    return(rc);
  }



  onCollectionSelected(file:any){
    this.network.extract_zip(file).subscribe((images:any)=>{
      this.tokens=images;
    });
  }



  async onFileSelected(files: any) {
    //tag: upload_file
    //Import/Upload des NFT: chargement depuis un fichier ou la fenetre
    if(files.hasOwnProperty("filename"))files=[files]
    let tags: any=null;
    let content;
    for(let f of files) {
      if(f.filename.startsWith("http")){
        let resp=await fetch(f.filename);
        let data=await resp.arrayBuffer();
        tags=ExifReader.load(data)      //voir https://www.npmjs.com/package/exifreader
      }

      if(f.filename.endsWith(".json")){
        const fr = new FileReader();
        fr.onload = () => {
          let fileContent = fr.result;
          if(typeof fileContent==="string"){
            content=JSON.parse(fileContent);
            $$("Ajout de "+content.name);
            this.tokens.push(content);
            this.local_save();
          }
        }
        fr.readAsText(f);
      }



      if(!tags) {
        let content = f.hasOwnProperty("file") ? f.file : f.src;
        try {
          if (!tags) tags = ExifReader.load(base64ToArrayBuffer(content.split("base64,")[1]))
        } catch (e) {}
      }

      let visual=f.file
      let _infos:any={};
      if(tags){
        if(tags.hasOwnProperty("mint")){
          const s_tmp=b64DecodeUnicode(tags.mint.value)
          _infos= JSON.parse(s_tmp);
        }

        if(_infos.hasOwnProperty("storage")){
          visual=_infos["storage"];
          //if(!visual.startsWith("http"))visual=environment.server+visual;
        }
      }

      this.tokens.push(this.get_token_from_xmp(_infos,visual))
    }
    this.local_save();
  }



  async confirm_mint(start=0,nb_tokens_to_mint=1){
    let price=Math.round((100*nb_tokens_to_mint*(this.user.price || environment.mint_cost.price_to_mint_one_token_in_crypto))/100);
    let price_in_fiat=Math.round((100*nb_tokens_to_mint*((this.user.price_in_fiat || environment.mint_cost.price_to_mint_one_token_in_fiat)))/100);
    let rep:any=await _ask_for_paiement(this,"NFLUCOIN-4921ed",
        price,
        price_in_fiat,
        this.user.merchant!,
        this.user.wallet_provider,
        "Confirmer le minage",
        "de "+nb_tokens_to_mint+" NFTs sur le réseau "+this.network.network+"<br>par le compte <strong>"+this.sel_key?.name+"</strong> dans la collection "+this.sel_collection?.name +" ?",
        "",
        this.user.profil.email,
        {contact: "contact@nfluent.io", subject: "Votre facture de minage", description:"Minage de "+nb_tokens_to_mint+" NFT"},
        this.user.buy_method)

    if(rep){
      this.user.init_wallet_provider(rep.data.provider);
      this.user.buy_method=rep.buy_method;
      showMessage(this,"Lancement du processus de minage");
      this.mintfile="sf_"+now()+".yaml";
      this.content_for_clipboard="";
      this.mint(start,nb_tokens_to_mint);
    } else {
      this.user.buy_method="";
      this.user.wallet_provider=undefined;
    }
  }


  //Fonction récurente appeler pour le minage en masse
  content_for_clipboard: string="";

  mint(index=0,nb_token_to_mint=1){
    if(index>=this.tokens.length || nb_token_to_mint<=0){
      showMessage(this,"Traitement terminé");
      wait_message(this,"");
    } else {
      let _t:NFT=this.tokens[index];
      if(!this.isValide(_t)){
        _t.price=this.price
        if(!_t.collection && this.sel_key)_t.collection={
          description: this.collection_name,
          link: "",
          options: [],
          owner: this.sel_key,
          price: undefined,
          roles: undefined,
          type: undefined,
          visual: undefined,
          id:this.collection_name,
          name:this.collection_name}
        _t.supply=this.quantity
        _t.message="hourglass:Minage";
        _t.creators=this.token_creators;
        wait_message(this,"Minage de "+_t.name+" ("+index+"/"+this.tokens.length+")");
        this.miner(_t).then((nft:any)=>{

          if(this.network.network?.startsWith("file")){
            this.content_for_clipboard=this.content_for_clipboard+"\t\t\t\t- "+nft.message+"\n"
            nft.message="miné";
            nft.address="";
          }
          this.local_save();
          this.mint(index+1,nb_token_to_mint-1);

        }).catch((result:any)=>{
          _t.message="Anomalie de minage: "+result.message;
        });
      } else {
        this.mint(index+1,nb_token_to_mint);
      }
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
    //target:this.sel_target,
    localStorage.setItem("miner_config",JSON.stringify({
      network:this.network.network,
      key:this.sel_key,
      platform:this.sel_platform,
      document_platform:this.sel_platform_document,
      collection:this.sel_collection,
      creators:this.token_creators,
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
      if(!this.sel_key){
        reject("no signature");
      }

      token.collection=this.sel_collection;

      if(this.isValide(token)==""){
        token.message="Minage en cours";
        if(this.network.network && this.network.network.startsWith("prestashop")){
          this.prestashop(token).subscribe((result:any)=>{
            showMessage(this,"NFT ajouter à prestashop");
            result.nft=token
            resolve(result);
          });
        }

        let error_message="";

        if(!this.sel_key)error_message="Vous devez avoir sélectionné une clé";
        if(error_message.length>0){
          showMessage(this,error_message);
          reject(error_message);
          token.message="Error: "+error_message;
        }

        if(this.sel_key && this.network.network){
          let id_operation=this.operation.sel_ope ? this.operation.sel_ope.id : "";

          token.owner=this.sel_key.address;

          // let target_network=this.sel_target.value;
          // if(target_network=="blockchain"){
          //   target_network=this.network.network;
          //   token.network=target_network;
          // }
          //
          let target_network=this.network.network;

          this.message="Minage du NFT '"+token.name+"'"
          this.network.mint(token,this.sel_key,token.owner || "",id_operation,this.sign, this.sel_platform.value,
              target_network,this.mintfile,
              this.encrypt_nft).then((result:any)=>{
            this.message="";
            if(!result.error || result.error==""){
              token.address=result.result.mint;
              token.links={
                explorer:result.link_mint,
                transaction: result.link_transaction,
                gallery:""
              }
              if(target_network=="file"){
                if(this.encrypt_nft)result.out="encrypt: \""+result.out+"\"";
                this.clipboard.beginCopy(result.out).copy();
                token.message=result.out;
              } else {
                token.message="NFT "+token.address+", minted for "+(Math.round(result.cost*10000)/10000)+" "+result.unity;
              }
              this.local_save();
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
        showMessage(this,"Minage impossible: "+this.isValide(token));
        reject(token);
      }
    });
  }


  find_name(creator: any): string {
    for(let k of this.network.keys)if(k.name && k.address==creator.address)return(k.name);
    return creator.address;
  }


  see_in_hub(nft:NFT) {
    if (!nft.address) return;
    open(nft.links?.explorer,"Explorer")
  }


  download_all(){
    if(this.tokens.length>0){
      this.network.archive(this.tokens).then((r:any)=>{
        if(r)open(r,"_blank");
      })
    }
  }

  eval_total_creator_sharing(){
    let rc=0;
    for(let c of this.token_creators)
      rc=rc+c.share;
    return rc;
  }

  add_creator(addr:string) : boolean {
    if(!this.isInCreators(this.token_creators,addr)){
      this.token_creators.push({
        address:addr,
        share: 100-this.eval_total_creator_sharing(),
        verified: true
      });
      this.set_creators();
      this.local_save();
      return true;
    }
    return false;
  }

  async ask_to_add_creator(){
    let addr:string=await _prompt(this,"Adresse email ou "+this.network.network+" du créateur à ajouter","","","text","Ok","Annuler",false);
    if(isEmail(addr)){
      this.network.create_account(this.network.network,addr,"mail_new_account_as_creator","mail_new_account_as_creator").subscribe((r:any)=>{
        this.add_creator(addr);
      })
    }else{
      this.add_creator(addr);
    }

  }

  add_miner_to_creator() {
    if(this.sel_key){
      this.token_creators.push({
        address:this.sel_key?.address,
        share: 100-this.eval_total_creator_sharing(),
        verified: true
      });
      this.set_creators();
    } else {
      showMessage(this,"Vous devez sélectionner un mineur")
      this.show_mint_section=true;
    }
  }

  remove(token: any) {
    let idx=this.tokens.indexOf(token);
    this.tokens.splice(idx,1);
    this.local_save();
  }


  isInCreators(l_creators:Creator[], addr="") : boolean {
    if(!this.sel_key)return false;
    if(addr.length==0)addr=this.sel_key?.address
    let miner_present=false;
    for(let c of l_creators){
      if(c.address==addr)miner_present=true;
    }
    return miner_present;
  }



  isValide(token: any):string {
    //vérifie la possibilité de miner les tokens
    if(this.sel_key?.balance==0)return "Le mineur ne dispose pas des fonds nécéssaires au minage"
    if(token.address && token.address.length>0)return "Ce token a déjà une adresse"
    if(token.properties){
      for(let f of token.properties.files){
        if(!f.uri.startsWith("http"))return("Au moins un des fichier attaché n'est pas partagé");
      }
      if(!token.image.startsWith("http"))return "Le visuel n'est pas partagé";
    }
    if(token.creators.length==0)return "Aucun créateur n'est déclaré pour ce NFT";
    if(token.name=="")return "Le NFT doit avoir un nom";

    if(token.visual=="")return "Le NFT doit avoir un visuel";
    if(!token.visual.startsWith("http"))return "Le visuel n'est pas en ligne";
    if(this.network.isElrond() && !token.collection)return "Le token doit être rataché à une collection";

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
        verified: false,
        address:this.sel_key?.address || "",
        share:100
      }];
    }
  }

  // set_marketplace(token: NFT) {
  //   if(token){
  //     token.marketplace={price:this.price,supply:this.quantity};
  //   }
  // }

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
    this.router.navigate(["collections"],{
      queryParams:{
        owner:this.user.addr,
        network:this.network.network
      }
    });
  }

  clear_attribute() {
    this.tokens[0].attributes=[];
  }

  clone_marketplace() {
    for(let i=1;i<this.tokens.length;i++){
      this.tokens[i].price=this.tokens[0].price;
      this.tokens[i].supply=this.tokens[0].supply;
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
        },(err)=>{showError(this,err)})
      }
    }
  }

  drop(files: File[],token:NFT) {
    //Intégration des fichiers attachés
    if(this.sel_platform_document.value && this.sel_platform_document.value!="nftstorage"){
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
          let _n: any = ope.mining?.networks[0];
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
                //let index=find(this.targets,{value:src.connexion,label:src.connexion},"value");
                //if(index>-1)this.sel_target=this.targets[index];
              }
            }
          } else {
            //this.sel_target=this.targets[0];
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
    //updatenetwork update_network
    this.network.network=$event;
    let param="network="+this.network.network
    if(this.sel_collection)param=param+"&collection="+this.sel_collection.id;
    this._location.replaceState("miner",param)
    this.token_creators=[];

    // if(!this.network.isBlockchain()){
    //   this.sel_key=newCryptoKey(this.user.profil.email,this.user.name)
    //
    //   let c:Creator={
    //     address: this.user.profil.email,
    //     verified: true,
    //     share: 100
    //   }
    //   this.token_creators.push(c);
    // }
  }

  async update_miner($event: any) {
    this.sel_key=$event;
    this.network.get_collections($event.address,this.network.network,false).subscribe((cols)=>{
      this.collections=cols;
      if(cols.length>0)this.changeCollection(this.collections[0]);
      this.local_save();
    })
  }

  changeCollection($event: any) {
    $$("Modification de la collection sélectionnée");
    this.sel_collection=$event
    for(let token of this.tokens){
      if(!token.address && this.sel_collection){
        token.collection=this.sel_collection;
      }
    }
  }

  show_file(filename: string) : string {
    if(filename.indexOf("f=")>-1)return(atob(filename.split("f=")[1]));
    if(filename.indexOf("filename=")>-1)return(filename.split("filename=")[1]);
    let pos=filename.lastIndexOf("/");
    return filename.substring(pos+1);
  }

  async new_collection() {
    if(this.sel_key){
      let cost='0.05 egld';
      let new_name=await _prompt(this,"Nom de votre collection","maCollect",
          "Pas d'espace et 20 caractères maximum (Coût de "+cost+")","text",
          "Créer","Annuler",false);
      let _col=newCollection(new_name,this.sel_key);
      if(_col){
        wait_message(this,"Création de la collection en cours");
        this.network.create_collection(_col).subscribe(async (r: any) => {
          wait_message(this);
          await this.user.init(this.sel_key!.address ,this.network.network, true);
          this.sel_collection=this.user.collections[0];
        },()=>{
          showError(this);
        })
      }
    }

  }

  async export_to_csv() {
    let filename=await _prompt(this,"Nom du fichier","mesNFTs","","text","Enregistrer","Annuler",false);
    let rc=[];
    for(let token of this.tokens){
      rc.push({
        name:token.name,
        visual: token.visual,
        description:token.description,
        address:token.address,
        message:token.message,
        tags:token.tags,
        symbol: token.symbol,
        network: token.network
      })
    }
    exportToCsv(filename+".csv",rc);
  }

  remove_creator(creator:Creator) {
    let pos=this.token_creators.indexOf(creator);
    this.token_creators.splice(pos,1)
    this.recalc_rate_except(null)
    this.local_save();
  }

  recalc_rate_except(creator: Creator | null) {
    if(this.token_creators.length<2 && creator){
      let pos=this.token_creators.indexOf(creator);
      this.token_creators[pos].share=100;
    }else{
      let total=this.eval_total_creator_sharing();
      let reste=1

      reste=100-total;
      if(creator){
        for(let c of this.token_creators){
          if(c.address!=creator.address)c.share=Math.round(c.share+reste/(this.token_creators.length-1));
          c.share=Math.max(0,Math.min(100,c.share));
        }
      }
      for(let i=0;i<this.token_creators.length;i++){
        this.token_creators[i].share=Math.min(Math.max(0,this.token_creators[i].share+(100-this.eval_total_creator_sharing())),100);
      }

    }
    for(let token of this.tokens){
      token.creators=this.token_creators;
    }
  }

    mintable() : number {
      let rc=0;
      for(let t of this.tokens){
        if(!t.address && this.isValide(t)=="")rc=rc+1;
      }
      return rc;
    }

  onpaid($event: any) {

  }

  login($event: { strong: boolean; nftchecked: boolean; address: string; provider: any }) {
    this.user.init($event.address,this.network.network,false,true);
  }
}
