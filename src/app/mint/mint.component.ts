import {Component,  OnInit} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {$$, base64ToArrayBuffer, MetabossKey, showError, showMessage, syntaxHighlight} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {PLATFORMS} from "../../definitions";
import {NetworkService} from "../network.service";
import {  Token} from "../nfts/nfts.component";
import ExifReader from 'exifreader';


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
  tokens: Token[]=[];
  keys: MetabossKey[]=[];
  platforms=PLATFORMS;
  sel_platform: string=this.platforms[1].value;


  constructor(
    public toast:MatSnackBar,
    public network:NetworkService,
    public dialog:MatDialog,
    public metaboss:MetabossService
  ) { }

  ngOnInit(): void {
    this.metaboss.keys().subscribe((keys)=>{this.keys=keys;})
    let tmp=localStorage.getItem("tokenstoimport");
    if(tmp)this.tokens=JSON.parse(tmp)
  }

  get_token_from_xmp(_infos:any,url:string) {
    let creators:any[]=[];
    if(this.metaboss.admin_key){
      creators.push(
        {
          address: this.metaboss.admin_key?.pubkey!,
          share:100,
          verified: 0
        }
      )
    }

    let attributes=[];
    let collection:any={};

    if(_infos.hasOwnProperty("properties")){
      for(let a of _infos.properties.split("\n")){
        attributes.push({trait_type:a.split("=")[0].trim(),value:a.split("=")[1].trim()})
      }
    }

    if(_infos.hasOwnProperty("collection")){
      collection={name:_infos.collection,family:_infos.family}
    }

    return(
    {
      address: "",
        metadataPDA: undefined,
      mint: "",
      network: this.network.network,
      search: {collection:"",metadata:""},
      splMintInfo: undefined,
        splTokenInfo: undefined,
      metadataOnchain: {
      key:0,
        updateAuthority:this.metaboss.admin_key?.pubkey.toString()!,
        mint:"",
        primarySaleHappened:0,
        isMutable:1,
        type:"tokenforge",
        data : {
        name:_infos.title,
          uri:"",
          sellerFeeBasisPoints:0,
          creators:creators,
          symbol: _infos.symbol
      }
    },
      metadataOffchain: {
        description:"",
          external_url:"",

          seller_fee_basis_points: 100,
          attributes:attributes,
          collection: collection,
          properties:{
          files:[],
            caterogy:"token",
            creators:creators
        },
        issuer:"",

          image: url,
          name: _infos.title,
      }
    });
  }



  onFileSelected(files: any) {
    if(typeof files=="object")files=[files];
    let index=0;
    for(let f of files) {
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

        this.upload_file({filename:f.filename,content:f.file,type:f.type}).then((url:any)=>{
          let _infos:any={};
          if(tags.hasOwnProperty("mint")){
            _infos= JSON.parse(atob(tags.mint.value));
          }
          this.tokens.push(this.get_token_from_xmp(_infos,url))
        })

      }
    }
  }

  mint(){
    for(let _t of this.tokens) {
      this.miner(_t);
    }
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

        let obj = {
          filename: file.filename,
          content: file.content,
          type:""
        }
        this.network.upload(obj,this.sel_platform).subscribe((r: any) => {
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


  upload_token(token: Token) {
    for(let file of token.metadataOffchain.properties.files){
      this.upload_file(file).then((r:any)=>{file.uri=r;})
    }
    this.upload_file({content:token.metadataOffchain.image,type:""}).then((r:any)=>{token.metadataOffchain.image=r;});
    setTimeout(()=>{this.local_save();},10000);
  }


  upload_all_tokens() {
    for(let token of this.tokens)
        this.upload_token(token);
    this.local_save();
  }



  miner(token: Token) {
    if(this.isValide(token)==""){
      this.metaboss.mint(token,this.sign,this.sel_platform).then(()=>{
        showMessage(this,"Token miné");
      }).catch((err)=>{
        showError(err);
      })
    } else {
      showMessage(this,"Minage impossible: "+this.isValide(token));
    }
  }


  find_name(creator: any): string {
    for(let k of this.keys)if(k.pubkey==creator.address)return(k.name);
    return creator.address;
  }


  to_string(token: any) {
    let rc=JSON.stringify(token,null,'\t');
    return rc;
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

  add_creator() {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Adresse du créateur ?",
          type: "text",
          result:this.metaboss.admin_key?.pubkey,
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((new_addr:string) => {
      if (new_addr){
        for(let t of this.tokens){
          t.metadataOffchain.properties.creators.push({
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
        if(c.address==this.metaboss.admin_key?.pubkey)canSign=true;
      }
      if(!canSign)return "Le miner ne fait pas parti des créateurs";
    }
    return "";
  }



  set_collection(token:any=null) {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Nom de la collection et de la famille (separé par /)",
          type: "text",
          result:"macollection/mafamille",
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((collection:string) => {
      if(collection){
        let name=collection.trim().split("/")[0].trim();
        let family=collection.indexOf("/")>-1 ? collection.split("/")[1].trim() : "";
        if(!token){
          for(let token of this.tokens){
            if(!token.metadataOffchain.collection){
              token.metadataOffchain.collection={name:name,family:family}
            }
          }
        } else {
          token.collection={name:name,family:family}
        }
      }
    })
  }

  onUploadXMP(file: any, token: Token) {
    let pos=this.tokens.indexOf(token);
    let xmp_data=atob(file.file.split("base64,")[1]).split("mint=")[1]
    xmp_data=xmp_data.substring(1).split("'")[0]
    let _infos=JSON.parse(atob(xmp_data))
    token=this.get_token_from_xmp(_infos,token.metadataOffchain.image);
    this.tokens[pos]=token;
  }
}
