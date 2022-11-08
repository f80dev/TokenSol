import {Component, OnInit} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {
  $$,  b64DecodeUnicode,
  base64ToArrayBuffer,
  getParams,now,
  showError,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {_prompt, PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {PLATFORMS} from "../../definitions";
import {NetworkService} from "../network.service";

import ExifReader from 'exifreader';
import {UserService} from "../user.service";
import {ActivatedRoute, Router} from "@angular/router";

import {OperationService} from "../operation.service";
import {NFT} from "../../nft";
import {Clipboard} from "@angular/cdk/clipboard";
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
  platforms=PLATFORMS;
  sel_platform: string=this.platforms[0].value;
  price: any=0;
  quantity: any=1;
  sel_collection: string="";
  mintfile: string="sf_"+now()+".yaml";

  constructor(
    public toast:MatSnackBar,
    public network:NetworkService,
    public dialog:MatDialog,
    public user:UserService,
    public operation:OperationService,
    public metaboss:MetabossService,
    public router:Router,
    public clipboard:Clipboard,
    public routes:ActivatedRoute,
  ) {

  }


  ngOnInit(): void {

    this.user.addr_change.subscribe((addr)=>{
      this.user.get_collection().then(()=>{
        this.sel_collection=this.user.collections[0].id || "";
      });
    })

    getParams(this.routes).then((params:any)=>{
      if(params.hasOwnProperty("collection")){
        this.sel_collection=params["collection"];
      }
    })
    this.init_form();
  }


  init_form(){
    if(this.user.isConnected(true)){
      let tmp=localStorage.getItem("tokenstoimport");
      if(tmp)this.tokens=JSON.parse(tmp);

      getParams(this.routes).then((params:any)=>{
        if(params.hasOwnProperty("files")){
          let files=[];
          for(let f of params["files"]){
            files.push({filename:f});
          }
          this.onFileSelected(files);
        }
      })
    } else this.user.login("Le minage nécessite une authentification");
  }



  get_token_from_xmp(_infos:any,url:string):NFT {
    let creators:any[]=[];
    if(this.user.key){
      creators.push(
        {
          address: this.user.key?.pubkey!,
          share:100,
          verified: 0
        }
      )
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


    let rc:NFT={
      collection: null,
      address: undefined,
      message:"",
      tags:_infos.tags,
      attributes: attributes,
      creators: creators,
      description: _infos.description,
      symbol: _infos.symbol,
      files: _infos.files.split("\n"),
      marketplace: {price:this.price,quantity:this.quantity},
      name: _infos.title,
      network: this.network.network,
      owner: undefined,
      royalties: 0,
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
        try {
          tags = ExifReader.load(base64ToArrayBuffer(f.file.split("base64,")[1]))
        } catch (e) {}

        let url=f.file;
        let _infos:any={};
        if(tags.hasOwnProperty("mint")){
          _infos= JSON.parse(b64DecodeUnicode(tags.mint.value));
        }
        this.tokens.push(this.get_token_from_xmp(_infos,url))
      }
    }
  }


  confirm_mint(){
    let nbtokens=this.tokens.length;
    _prompt(this,
      "Confirmer le minage","",
      "html:... de "+nbtokens+" NFTs sur le réseau "+this.network.network+"<br>par le compte <strong>"+this.user.key?.name+"</strong> dans la collection "+this.sel_collection +" ?",
      "","Ok","Annuler",true
      ).then((rep)=>{
        if(rep=="yes"){
          showMessage(this,"Lancement du processus de minage");
          this.mintfile="sf_"+now()+".yaml";
          this.network.wait("Production du fichier");
          this.mint(0);
          // setTimeout(()=>{
          //   this.network.wait();
          //   open(environment.server+"/api/images/"+this.mintfile,"mintfile")
          // },5000);

        }
    });
  }


  //Fonction récurente appeler pour le minage en masse
  complement: string="";

  mint(index=0){
    this.set_collection();
    let _t:NFT=this.tokens[index];
    _t.marketplace={price:this.price,quantity:this.quantity}
    _t.message="hourglass:Minage";
    showMessage(this,"Minage de "+_t.name);

    this.miner(_t).then((nft:any)=>{
      _t.message=nft.message;
      if(this.tokens.length>index){
        this.mint(index+1);
      }
    }).catch((result:any)=>{
      _t.message="Anomalie de minage: "+result.message;
    });
  }


  clear() {
    $$("Effactement des tokens")
    this.tokens=[];
    this.local_save();
  }



  local_save(){
    localStorage.setItem("tokenstoimport",JSON.stringify(this.tokens));
  }


  upload_file(file:any){
    return new Promise((resolve, reject) => {
      file.type="image/webp";
      this.network.upload(file,this.sel_platform,file.type).subscribe((r: any) => {
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
    this.upload_file({content:token.visual,type:""}).then((r:any)=>{
      token.visual=r;
      token.message="visual uploaded";
    });

  }


  upload_all_tokens() {
    for(let i=0;i<this.tokens.length;i++){
      setTimeout(()=>{
        this.network.wait("Upload de "+i+"/"+this.tokens.length+" en cours");
        this.upload_token(this.tokens[i]);
        if(i==this.tokens.length-1){
          this.local_save();
          this.network.wait("");
        }
      },i*2000);
    }
  }


  //Opére le minage.
  //Cette fonction est à la fois utilisé par le process récurent en masse et le process individuel
  create_options: any=[
    {label:"Create",value:"ESDTRoleNFTCreate"},
    {label:"Burn",value:"ESDTRoleNFTBurn"},
    {label:"Update",value:"ESDTRoleNFTUpdateAttributes"},
    {label:"Add URI",value:"ESDTRoleNFTAddURI"},
    {label:"TransferRole",value:"ESDTTransferRole"}
  ]


  miner(token: NFT) : Promise<any> {
    return new Promise<any>((resolve, reject) => {
      if(this.user.key==undefined){
        reject("no signature");
      }
      if(this.isValide(token)==""){
        token.message="Minage en cours";
        if(this.network.network.startsWith("prestashop")){
          this.prestashop(token).subscribe((result:any)=>{
            showMessage(this,"NFT ajouter à prestashop");
            result.nft=token
            resolve(result);
          });
        }

        let error_message="";
        if(!token.visual.startsWith("https"))error_message="Le visuel n'est pas en ligne";
        if(!this.user.key)error_message="Vous devez avoir sélectionné une clé";
        if(error_message.length>0){
          showMessage(this,error_message);
          reject(error_message);
          token.message="Error: "+error_message;
        }

        if(this.user.key){
          token.collection=this.user.find_collection(this.sel_collection);
          this.network.mint(token,this.user.key.name,this.user.key.name,this.sign, this.sel_platform,this.network.network,this.mintfile).then((result:any)=>{
            if(!result.error || result.error==""){
              resolve(token);
              token.address=result.result.mint;
              if(this.network.network=="file"){
                this.clipboard.copy(result.out);
                token.message="Le code est dans votre presse-papier"
              } else {
                token.message="Minted for "+result.cost+" "+result.unity;
              }
            } else {
              token.message=result.error;
              reject(result.error);
            }
          }).catch((err)=>{
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
    for(let k of this.metaboss.keys)if(k.pubkey==creator.address)return(k.name);
    return creator.address;
  }


  see_in_hub(nft:NFT){
    this.network.open_gallery(nft.address);
  }

  to_string(token: any) {

  }

  download(token: any) {

  }

  copy(token:any){

  }


  download_all(){
    if(this.tokens.length>0){
      this.metaboss.archive(this.tokens).then((r:any)=>{
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
              address:this.user.key?.pubkey,
              share:Number(royalties)
            });
          } else {
            t.creators.push({
              verified: 0,
              address:this.user.key?.pubkey,
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
          result:this.user.key?.pubkey,
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
        if(c.address==this.user.key?.pubkey)canSign=true;
      }
      if(!canSign)return "Le miner ne fait pas parti des créateurs";
    }
    return "";
  }



  set_collection() {
    if(this.sel_collection.length>0){
      let col=this.user.find_collection(this.sel_collection);
      for(let token of this.tokens){
        token.collection=col;
      }
    }
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
    showMessage(this,"Network changed")
  }


  reset_creator() {
    for(let t of this.tokens){
      t.creators=[{
        verified: 0,
        address:this.user.key?.pubkey,
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
}
