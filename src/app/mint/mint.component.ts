import {Component,  OnInit} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {$$, base64ToArrayBuffer, MetabossKey, showError, showMessage, syntaxHighlight} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {PLATFORMS} from "../../definitions";
import {NetworkService} from "../network.service";
import {  NFT} from "../nfts/nfts.component";
import ExifReader from 'exifreader';
import {UserService} from "../user.service";
import {ActivatedRoute} from "@angular/router";
import {Operation} from "../../operation";
import {NUMPAD_NINE} from "@angular/cdk/keycodes";


@Component({
  selector: 'app-mint',
  templateUrl: './mint.component.html',
  styleUrls: ['./mint.component.css']
})
export class MintComponent implements OnInit {

  fileName: string="";
  key: string="";
  formData: FormData=new FormData();
  sel_ope:any;
  sign: boolean=false;
  tokens: NFT[]=[];
  platforms=PLATFORMS;
  sel_platform: string=this.platforms[0].value;
  price: any=0;
  quantity: any=1;
  seller_fee_basis_points: any=0;


  constructor(
    public toast:MatSnackBar,
    public network:NetworkService,
    public dialog:MatDialog,
    public user:UserService,
    public metaboss:MetabossService,
    public routes:ActivatedRoute,
  ) { }



  ngOnInit(): void {
    if(this.user.isConnected()){
      let tmp=localStorage.getItem("tokenstoimport");
      if(tmp)this.tokens=JSON.parse(tmp)
      this.network.get_operations(this.routes.snapshot.queryParamMap.get("ope") || "").subscribe((r:any)=>{
        this.sel_ope=r;
      })
    } else this.user.login("Le minage nécessite une authentification");

  }



  get_token_from_xmp(_infos:any,url:string):NFT {
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

    let attributes:any[]=[];
    let collection:any={};

    if(_infos.hasOwnProperty("properties")){
      for(let a of _infos.properties.split("\n")){
        attributes.push({trait_type:a.split("=")[0].trim(),value:a.split("=")[1].trim()})
      }
    }

    if(_infos.hasOwnProperty("collection")){
      collection={name:_infos.collection,family:_infos.family}
    }


    let rc:NFT={
      address: undefined,
      message:"",
      attributes: attributes,
      collection: collection,
      creators: creators,
      description: "",
      files: [],
      marketplace: {price:this.price,quantity:this.quantity},
      name: _infos.title,
      network: this.network.network,
      owner: undefined,
      royalties: 0,
      symbol: "",
      visual: url,
      solana:null
    }

    return(rc);
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


  confirm_mint(){
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Confirmer le minage",
          question: "html:... de "+this.tokens.length+" NFTs sur le réseau "+this.network.network+" par le compte <strong>"+this.metaboss.admin_key?.name+"</strong> ?",
          onlyConfirm:true,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((rep:string) => {
      if(rep=="yes"){
        showMessage(this,"Lancement du processus de minage");
        this.mint(0);
      }
    });
  }


  mint(index=0){
    let _t:NFT=this.tokens[index];
    _t.marketplace={price:this.price,quantity:this.quantity,royalties:this.seller_fee_basis_points*100}
    _t.message="hourglass:Minage";
    showMessage(this,"Minage de "+_t.name);
    this.miner(_t).then((t)=>{
      _t.message="Miné";
      if(this.tokens.length>index){
        this.mint(index+1);
      }
    }).catch(()=>{
      _t.message="Anomalie";

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


  upload_token(token: NFT) {
    for(let file of token.files){
      this.upload_file(file).then((r:any)=>{file.uri=r;})
    }
    this.upload_file({content:token.visual,type:""}).then((r:any)=>{token.visual=r;});
    setTimeout(()=>{this.local_save();},10000);
  }


  upload_all_tokens() {
    for(let token of this.tokens)
      this.upload_token(token);
    this.local_save();
  }



  miner(token: NFT) {
    return new Promise((resolve, reject) => {
      if(this.isValide(token)==""){
        this.metaboss.mint(token,this.sign,this.sel_platform).then(()=>{
          showMessage(this,"Token miné");
          resolve(token);
        }).catch((err)=>{
          showError(err);
        })
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

  add_miner_to_creator(){
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Royalties pour "+this.metaboss.admin_key?.name,
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
              address:this.metaboss.admin_key?.pubkey,
              share:Number(royalties)
            });
          } else {
            t.creators.push({
              verified: 0,
              address:this.metaboss.admin_key?.pubkey,
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
          result:this.metaboss.admin_key?.pubkey,
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
            if(!token.collection){
              token.collection={name:name,family:family}
            }
          }
        } else {
          token.collection={name:name,family:family}
        }
      }
    })
  }

  onUploadXMP(file: any, token: NFT) {
    let pos=this.tokens.indexOf(token);
    let xmp_data=atob(file.file.split("base64,")[1]).split("mint=")[1]
    xmp_data=xmp_data.substring(1).split("'")[0]
    let _infos=JSON.parse(atob(xmp_data))
    token=this.get_token_from_xmp(_infos,token.visual);
    this.tokens[pos]=token;
  }

  prestashop() {
    this.network.wait("Envoi des NFTs");
    let idx=0;
    for(let token of this.tokens){
      idx=idx+1;
      token.royalties=this.seller_fee_basis_points*100;
      token.network=this.network.network;
      if(token.symbol.length==0)token.symbol="NFT"+idx.toString(16);
      token.marketplace={price:this.price,quantity:this.quantity}
    }
    this.network.export_to_prestashop(this.sel_ope.id,this.tokens).subscribe(()=>{
      this.network.wait();
      showMessage(this,"NFT transmis");
    })
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
        address:this.metaboss.admin_key?.pubkey,
        share:100
      }];
    }
  }
}
