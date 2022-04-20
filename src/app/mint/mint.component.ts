import {Component,  OnInit} from '@angular/core';
import {MetabossService} from "../metaboss.service";
import {$$, MetabossKey, showError, showMessage, syntaxHighlight} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {QUOTA} from "../../definitions";

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
  tokens: any[]=[];
  keys: MetabossKey[]=[];
  platforms=[
    {label:"NFT storage",value:"nftstorage"},
    {label:"IPFS",value:"ipfs"},
    {label:"Infura (IPFS)",value:"infura"}
  ]
  sel_platform: string=this.platforms[0].value;


  constructor(
    public toast:MatSnackBar,
    public dialog:MatDialog,
    public metaboss:MetabossService
  ) { }

  ngOnInit(): void {
    this.metaboss.keys().subscribe((keys)=>{this.keys=keys;})
    let tmp=localStorage.getItem("tokenstoimport");
    if(tmp)this.tokens=JSON.parse(tmp)
  }

  onFileSelected(evt: Event) {
    let target: any = evt?.target;
    for(let f of target.files) {
      if(f.name.endsWith(".json")){
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
        const reader = new FileReader();
        reader.onload = (event) => {
          // @ts-ignore
          if(reader.result?.length<QUOTA){
            // @ts-ignore
            localStorage.setItem("attach_file_"+f.name,reader.result)
          }
        }
        reader.readAsDataURL(f);
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
      if(file.uri.indexOf("http")!=0) {
        let obj = {
          filename: file.uri,
          content: localStorage.getItem("attach_file_" + file.uri)
        }
        this.metaboss.upload(obj,this.sel_platform).then((r: any) => {
          localStorage.removeItem("attach_file_" + file.uri);
          resolve(r.url)
          showMessage(this, "upload ok");
          this.local_save();
        }).catch((err) => {
          showError(err);
          reject(err);
        })
      }
    });
  }


  upload_token(token: any) {
    for(let file of token.properties.files){
      this.upload_file(file).then((r)=>{file["uri"]=r;})
    }
    this.upload_file({uri:token.image}).then((r)=>{token.image=r;});
    setTimeout(()=>{this.local_save();},10000);
  }


  upload_all_tokens() {
    for(let token of this.tokens)
        this.upload_token(token);
    this.local_save();
  }



  miner(token: any) {
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
          t.properties.creators.push({
            address:new_addr,
            verified:false,
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
    for(let f of token.properties.files){
      if(!f.uri.startsWith("http"))return("Au moins un des fichier attaché n'est pas partagé");
    }
    if(!token.image.startsWith("http"))return "Le visuel n'est pas partagé";
    let canSign=false;
    for(let c of token.properties.creators){
      if(c.address==this.metaboss.admin_key?.pubkey)canSign=true;
    }
    if(!canSign)return "Le miner ne fait pas parti des créateurs";
    return "";
  }

  change_name(token: any) {
    this.dialog.open(PromptComponent,{
      width: 'auto',data:
        {
          title: "Nouveau nom",
          type: "text",
          result:token.name,
          onlyConfirm:false,
          lbl_ok:"Ok",
          lbl_cancel:"Annuler"
        }
    }).afterClosed().subscribe((new_name:string) => {
      if (new_name){
        token.name=new_name;
        this.local_save();
      }
    });
  }
}
