import {Component, EventEmitter, Input, OnChanges, OnInit, Output, SimpleChanges} from '@angular/core';
import {NetworkService} from "../network.service";
import {PublicKey} from "@solana/web3.js";
import {$$, showError, showMessage, toStringify} from "../../tools";
import {PromptComponent} from "../prompt/prompt.component";
import {MatDialog} from "@angular/material/dialog";
import {MetabossService} from "../metaboss.service";
import {MatSnackBar} from "@angular/material/snack-bar";


@Component({
  selector: 'app-nfts',
  templateUrl: './nfts.component.html',
  styleUrls: ['./nfts.component.css']
})
export class NftsComponent implements OnInit {

  @Input("nfts") nfts: any;
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
    this.metaboss.burn(nft.accountInfo.mint,this.network.network).then(success=>{
      if(success)this.onrefresh.emit();
    }).catch(err => {showError(this,err)})


  }



  update_field(attr: any, nft: any) {
    this.ask_for_attribute(attr.value,attr.trait_type).then(new_value=>{
      for(let i=0;i<nft.offchain.attributes.length;i++){
        if(nft.offchain.attributes[i]==attr){
          nft.offchain.attributes[i].value=new_value;
          break;
        }
      }
        this.network.wait("Modification en cours");
        this.metaboss.update_obj(nft.accountInfo.mint,nft.offchain,this.network.network).then(success=>{
          this.network.wait("");
          showMessage(this,"Modification effectuée, un délai peut être nécéssaire avant validation par la blockchain");
        })
      })
  }

  get_explorer(address: string) {
      return 'https://solscan.io/address/'+address+'?cluster=devnet';
  }


  sign_token(nft: any, creator: any) {
    this.network.wait("Signature en cours");
    this.metaboss.sign(nft.accountInfo.mint.toBase58(),creator.address,this.network.network).then(()=>{
      showMessage(this,nft.offchain.name+" signé. Mise a jour de la blockchain en cours");
      this.network.wait("");
      setTimeout(()=>{this.onrefresh.emit();},4000);
    });
  }



  ngOnInit(): void {
    this.metaboss.keys().subscribe((keys)=>{
      this.network.keys=keys;
    })
  }
}
