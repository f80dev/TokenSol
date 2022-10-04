import {Component, OnDestroy, OnInit} from '@angular/core';
import {ActivatedRoute, Router} from "@angular/router";
import {NetworkService} from "../network.service";
import {$$, decrypt, getParams, hasWebcam, showError, showMessage} from "../../tools";
import {MatSnackBar} from "@angular/material/snack-bar";
import {AliasPipe} from "../alias.pipe";
import {Location} from "@angular/common";
import {UserService} from "../user.service";
import {NFT} from "../../nft";
import {NFLUENT_WALLET} from "../../definitions";

@Component({
  selector: 'app-dealermachine',
  templateUrl: './dealermachine.component.html',
  styleUrls: ['./dealermachine.component.css']
})
export class DealermachineComponent implements OnInit {
  address: string="";
  wallet_link: string="";
  nft:NFT | null=null;
  final_message="";
  ope: any=null;
  webcam: boolean=true;
  mining: any={};
  authentification: any;

  constructor(
    public routes:ActivatedRoute,
    public _location:Location,
    public userService:UserService,
    public network:NetworkService,
    public toast:MatSnackBar,
    public router:Router,
    public alias:AliasPipe
  ) { }


  ngOnInit(): void {
    hasWebcam(this.webcam);

    getParams(this.routes).then((params:any)=>{
      this.nft=params["token"];
      let ope=params["ope"];
      let section=params["section"];

      if(!this.nft){
        $$("On va chercher les NFTs dans le fichier d'opération");
        let address=params["address"] || "";
        let symbol=params["symbol"] || "";
        this.network.get_nfts_from_operation(ope).subscribe((r:any)=>{
          for(let nft of r["nfts"]){
            if((nft.address==address && address.length>0) || (nft.symbol==symbol && nft.address?.length==0))this.nft=nft;
          }
        });
      }

      this.mining=params["mining"];
      this.selfWalletConnexion=params["selfWalletConnexion"] || (section=="lottery");

      if(ope){
        this.network.get_operations(ope).subscribe((ope:any)=>{
          this.ope=ope;
          this.mining=params["mining"] || this.ope.lazy_mining;
          if(section){
            this.authentification=this.ope[section].authentification;
          }
        })
      }

    })
  }

  //http://127.0.0.1:4200/dealermachine/?ope=calvi2022
  message: string="";
  hasWebcam=true;
  billing_address="";
  selfWalletConnexion: boolean=false;

  lost(){
    $$("Lost")
    if(this.ope && this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.looser.message,this.ope.lottery.end_process.looser.redirection)
    } else {
      this.end_process("Ce NFT vous a échapé");
    }
  }

  win(){
    $$("Win")
    if(this.ope && this.ope.lottery.hasOwnProperty("end_process")){
      this.end_process(this.ope.lottery.end_process.winner.message,this.ope.lottery.end_process.winner.redirection)
    } else {
      this.end_process("Ce NFT est le votre.");
    }
  }

  end_process(sMessage:string,rediction=null){
    if(rediction){
      showMessage(this,sMessage);
      setTimeout(()=>{
        open(this.ope.lottery.end_process.winner.redirection);
        },3500);
    } else {
      this.message=sMessage+". Vous pouvez fermer cette écran";
    }
  }


  valide(addr:any) {
    if(addr.hasOwnProperty("addr"))addr=addr.addr;
    this.address=addr.replace("'","");
    addr=this.alias.transform(addr,"pubkey");
    if(this.nft!.address?.startsWith("db_")){
      $$("Ce token est issue d'une base de données, donc non miné");;
      if(this.ope)this.message=this.ope.store.support.buy_message;
      this.network.mint_for_contest(addr,this.ope.id,this.mining.miner,this.mining.metadata_storage,this.mining.network,this.nft!).subscribe((r:any)=>{;
        this.message="";
        if(r.error.length>0){
          this.message=r.error+". ";
        } else {
          this.win();
        }
      },(err:any)=>{
        showError(this,err);
        this.message="";
      })
    }else{
      $$("Ce token est déjà miné, on se contente de le transférer");
      if(this.nft!.address!=""){
        let mint_addr=this.nft!.address || "";
        let owner=this.nft!.owner || "";
        this.message="Envoi en cours";
        this.network.transfer_to(mint_addr,addr,owner).subscribe((r:any)=>{
          this.message="";
          this.wallet_link=NFLUENT_WALLET+"?"+r.nfluent_wallet;
          this.final_message="Retrouver votre nouveau NFT dans votre wallet NFluenT";
        },(err:any)=>{
          showMessage(this,"Impossible d'envoyer ce NFT");
          this.final_message="Problème technique: Envoi du NFT annulé";
        })
      }
    }
  }

  onLoadPaymentData($event: any) {
    if($event.returnValue)
      this.valide(this.address);
  }

  onflash($event: any) {
    this.address=$event.data;
  }

  cancel() {
    this.final_message="Annulation. Vous pouvez fermer cette fenêtre";
  }

  validate_input_address() {
    if(this.address && this.address.indexOf("@")==-1 && !this.address.startsWith('\'') && !this.network.isElrond(this.address)){
      showMessage(this,"Le service n'est compatible qu'avec les adresses elrond");
    } else {
      this.valide(this.address);
    }
  }
}
