import {Component,  OnInit} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {
  $$, b64DecodeUnicode,
  base64ToArrayBuffer,
  getParams,
  isLocal,
  showError,
  showMessage
} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {PLATFORMS} from "../../definitions";
import {NetworkService} from "../network.service";
import {  NFT} from "../nfts/nfts.component";
import ExifReader from 'exifreader';
import {UserService} from "../user.service";
import {ActivatedRoute} from "@angular/router";
import {environment} from "../../environments/environment";
import {OperationService} from "../operation.service";


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
  seller_fee_basis_points: any=0;
  collection: string="";


  constructor(
    public toast:MatSnackBar,
    public network:NetworkService,
    public dialog:MatDialog,
    public user:UserService,
    public operation:OperationService,
    public metaboss:MetabossService,
    public routes:ActivatedRoute,
  ) { }



  ngOnInit(): void {
    if(this.user.isConnected()){
      this.metaboss.init_keys(this.network.network,false);
      let tmp=localStorage.getItem("tokenstoimport");
      if(tmp)this.tokens=JSON.parse(tmp)
      if(this.collection.length==0 && this.tokens.length>0)this.collection=this.tokens[0].collection;

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
        if(a.length>1){
          attributes.push({trait_type:a.split("=")[0].trim(),value:a.split("=")[1].trim()})
        }
      }
    }

    if(_infos.hasOwnProperty("collection")){
      collection=_infos.collection
    }


    let rc:NFT={
      address: undefined,
      message:"",
      attributes: attributes,
      collection: collection,
      creators: creators,
      description: _infos.description,
      symbol: _infos.symbol,
      files: [],
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
        if(this.collection.length==0)this.collection=this.tokens[0].collection;

        // this.upload_file({filename:f.filename,content:f.file,type:f.type}).then((url:any)=>{
        //
        // });

      }
    }
  }


  confirm_mint(){
    let nbtokens=this.tokens.length;
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Confirmer le minage",
          question: "html:... de "+nbtokens+" NFTs sur le réseau "+this.network.network+" par le compte <strong>"+this.metaboss.admin_key?.name+"</strong> ?",
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


  //Fonction récurente appeler pour le minage en masse
  complement: string="";

  mint(index=0){
    this.set_collection();
    let _t:NFT=this.tokens[index];
    _t.marketplace={price:this.price,quantity:this.quantity}
    _t.royalties=this.seller_fee_basis_points*100;
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
    this.upload_file({content:token.visual,type:""}).then((r:any)=>{token.visual=r;});
    token.message="visual uploaded";
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
  miner(token: NFT) : Promise<any> {
    return new Promise<any>((resolve, reject) => {
      if(this.metaboss.admin_key==undefined){
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

        this.metaboss.mint(token,this.sign, this.sel_platform,this.network.network).then((result:any)=>{
          if(!result.error || result.error==""){
            token.message="Minted for "+result.cost+" "+result.unity;
            resolve(token);
          } else {
            token.message="Mint error";
            reject(result.error);
          }
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



  set_collection() {
    for(let token of this.tokens){
      token.collection=this.collection;
      //if(token.collection.indexOf("/")==-1)token.collection=token.collection+"/nfluent";
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
    return this.network.export_to_prestashop(this.operation.sel_ope!.id,token,false);
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

  set_marketplace(token: NFT) {
    if(token){
      token.marketplace={price:this.price,quantity:this.quantity};
    }
  }
}
