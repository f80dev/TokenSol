import {Component, EventEmitter, Input,  OnInit, Output} from '@angular/core';
import {NetworkService} from "../network.service";
import {getExplorer, showError, showMessage} from "../../tools";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {MetabossService} from "../metaboss.service";
import {MatSnackBar} from "@angular/material/snack-bar";

export interface Creator {
  address:string
  verified:number
  share:number
}
export interface SplTokenInfo {
  mint:string
  owner:string
  amount: number
  state:number
  address:string
  isFrozen:boolean
}
export interface SplMintInfo {
  mintAuthority:string
  supply:string
  decimal:number
}
export interface Attribute {
  trait_type:string
  value:string
}
export interface MetadataExternal {
  name:string
  description:string
  external_url:string
  image: string
  seller_fee_basis_points: number
  attributes:Attribute[]
  collection: {
    name:string
    family:string | undefined
  }
  properties:{
    files:{uri:string,type:string}[]
    caterogy:string
    creators:Creator[]
  }
  issuer:string
}

export interface MetadataOnChain {
  key:number | undefined
  updateAuthority:string
  mint:string,
  primarySaleHappened:number
  isMutable:number
  type:string
  data:{
    name:string
    symbol:string
    uri:string
    sellerFeeBasisPoints:number
    creators:Creator[]
  }
}
export interface Search {
  collection:string
  metadata:string
}

export interface NFT {
  collection:any
  symbol:string
  network: string | undefined
  attributes:any[]
  name:string
  description:string
  visual:string
  creators:any[]
  address:string | undefined
  royalties:number
  owner:string | undefined
  marketplace:any | undefined
  files:any[]
}

export interface SolanaToken {
  mint:string,
  network: string
  address: string,
  splTokenInfo : SplTokenInfo | undefined
  splMintInfo : SplMintInfo | undefined,
  metadataPDA:any,
  metadataOnchain:MetadataOnChain,
  metadataOffchain:MetadataExternal,
  search:Search
}

@Component({
  selector: 'app-nfts',
  templateUrl: './nfts.component.html',
  styleUrls: ['./nfts.component.css']
})
export class NftsComponent implements OnInit {

  @Input("nfts") nfts: any[]=[];
  @Input("user") user: string | undefined;
  @Input("format") format: string="str";
  @Output('refresh') onrefresh: EventEmitter<any>=new EventEmitter();

  constructor(
    public network:NetworkService,
    public dialog:MatDialog,
    public toast:MatSnackBar,
    public metaboss:MetabossService
  ) {}


  // toString(tokenInfo:any,sep="\n"){
  //   let s=toStringify(tokenInfo)
  //   for(let i=0;i<20;i++){
  //     s=s.replace("\",\"","\""+sep+"\"")
  //     s=s.replace("{\"","{"+sep+"\"").replace("\"}","\""+sep+"}")
  //   }
  //
  //   if(this.format=="html"){
  //     for(let v of Object.values(tokenInfo)){
  //       // @ts-ignore
  //
  //       if(v?.constructor.name=="PublicKey"){
  //         // @ts-ignore
  //         let addr=v.toBase58().trim();
  //         s=s.replace(addr,"<a target=_blank href='https://solscan.io/account/"+addr+"?cluster="+this.network.network+"'>"+addr+"</a>");
  //       }
  //     }
  //   }
  //
  //   return s;
  // }



  // ngOnChanges(changes: SimpleChanges): void {
  //   if(changes["nfts"]["currentValue"] && changes["user"]["currentValue"]){
  //     let sep="\n";
  //     this.nfts_out=this.nfts;
  //     if(this.format=="str")sep="\n";
  //     if(this.format=="html")sep="<br>";
  //     if(this.format=="html" || this.format=="str")this.nfts_out=this.nfts.map((x:any) => this.toString(x,sep))
  //   }
  // }


  ask_for_attribute(default_value:any,title:string) {
    return new Promise((resolve, reject) => {
      this.dialog.open(PromptComponent,{
        width: 'auto',data:
          {
            title: "Modification de "+title,
            type: "text",
            value:default_value,
            placeholder:"Valeur actuelle: "+default_value,
            onlyConfirm:false,
            lbl_ok:"Ok",
            lbl_cancel:"Annuler"
          }
      }).afterClosed().subscribe(resp => {
        if(resp)
          resolve(resp);
        else
          reject(resp);
      });
    });
  }

  update(nft: any) {

  }


  burn(nft:any) {
    if(nft.metadataOnchain.isMutable==0){
      showMessage(this,"Ce NFT n'est plus modifiable");
      return;
    }
    this.metaboss.burn(nft.address,this.network.network).then(success=>{
      if(success)this.onrefresh.emit();
    }).catch(err => {
      showError(this,err)
    })
  }



  update_field(attr: any, nft: any) {

    if(nft.metadataOnchain?.isMutable==0){
      showMessage(this,"Ce NFT n'est plus modifiable");
      return;
    }

    // if(nft.metadataOnchain?.updateAuthority!=this.metaboss.admin_key?.pubkey){
    //   showMessage(this,"Cette signature ne permet pas la mise a jour du NFT");
    //   return;
    // }

    this.ask_for_attribute(attr.value,attr.trait_type).then((new_value:any)=>{
      for(let i=0;i<nft.metadataOffchain?.attributes.length;i++){
        if(nft.metadataOffchain?.attributes[i]==attr){
          nft.metadataOffchain.attributes[i].value=new_value;
          break;
        }
      }
        this.network.wait("Modification en cours");
        this.metaboss.update_obj(nft.address,nft.metadataOffchain,this.network.network).then(success=>{
          this.network.wait("");
          showMessage(this,"Modification effectuée, un délai peut être nécéssaire avant validation par la blockchain");
        }).catch((err)=>{
          showMessage(this,err);
        })
      })
  }

  getSolanaExplorer(id:string | undefined) {
    return getExplorer(id,this.network.network);
  }

  use_token(nft:any){
    this.network.wait("Utilisation en cours");
    this.metaboss.use(nft.address,this.network.network).then(()=>{
      showMessage(this,nft.metadataOnchain.data.name+" utilisé. Mise a jour de la blockchain en cours");
      this.network.wait("");
    });
  }

  sign_token(nft: any,creator:Creator) {
    this.network.wait("Signature en cours");
    this.metaboss.sign(nft.address,creator.address,this.network.network).then(()=>{
      showMessage(this,nft.metadataOnchain.data.name+" signé. Mise a jour de la blockchain en cours");
      this.network.wait("");
      setTimeout(()=>{this.onrefresh.emit();},4000);
    });
  }



  ngOnInit(): void {

  }



  trunc_string(value: string,size=60) {
    if(!value)return(value);
    value=value.toString();
    return value.substring(0,Math.min(size,value.length));
  }
}
